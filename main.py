import http.server
import socketserver
import urllib.parse
import json
import os
import uuid
from http import cookies
from core.user import User
from core.coupon import Coupon
from core.ds_manager import DataManager
from core.database import load_data, save_data

PORT = 8080
DATA_MGR = DataManager()

# Pre-load data
load_data(DATA_MGR)

# Create Admin if not exists
if not DATA_MGR.get_user("admin"):
    DATA_MGR.add_user(User("admin", "admin123", is_admin=True))

class CouponXHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse URL
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query = urllib.parse.parse_qs(parsed_path.query)

            # Static files
            if path.startswith("/public/"):
                super().do_GET()
                return

            print(f"GET request to {path}")

            # Simple Routing
            if path == "/" or path == "/login":
                self.serve_template("login.html")
            elif path == "/register":
                self.serve_template("register.html") 
            elif path == "/dashboard":
                self.handle_dashboard()
            elif path == "/give":
                self.handle_give_page()
            elif path == "/take":
                self.handle_take_page(query)
            elif path == "/my_coupons":
                self.handle_my_coupons()
            elif path == "/admin":
                self.handle_admin_dashboard()
            elif path == "/logout":
                self.handle_logout()
            else:
                self.send_error(404, "Page Not Found")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {e}")

    def do_POST(self):
        try:
            # Parse Form Data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            path = self.path

            print(f"POST request to {path} with params: {params}")

            if path == "/login":
                self.handle_login(params)
            elif path == "/register":
                self.handle_register(params)
            elif path == "/add_coupon":
                self.handle_add_coupon(params)
            elif path == "/claim_coupon":
                self.handle_claim_coupon(params)
            elif path == "/admin/delete_user":
                self.handle_admin_delete_user(params)
            elif path == "/admin/delete_coupon":
                self.handle_admin_delete_coupon(params)
            else:
                self.send_error(404, "Endpoint Not Found")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Internal Server Error: {e}")

    # --- Helpers ---
    
    def serve_html(self, content):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def serve_template(self, template_name, context=None):
        if context is None:
            context = {}
            
        try:
            with open(f"templates/{template_name}", "r", encoding="utf-8") as f:
                template = f.read()
                
            # Very basic templating (replace {{ key }} with value)
            for key, value in context.items():
                template = template.replace(f"{{{{ {key} }}}}", str(value))
                
            # Handle list rendering manually for specific templates if needed
            # For this simple project, I might just construct HTML strings in Python for lists
            
            self.serve_html(template)
        except FileNotFoundError:
            self.send_error(404, f"Template {template_name} not found")

    def get_session_user(self):
        # Simple cookie check
        if "Cookie" in self.headers:
            c = cookies.SimpleCookie(self.headers["Cookie"])
            if "user" in c:
                username = c["user"].value
                return DATA_MGR.get_user(username)
        return None

    def redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    # --- Handlers ---

    def handle_login(self, params):
        username = params.get("username", [""])[0]
        password = params.get("password", [""])[0]
        
        user = DATA_MGR.get_user(username)
        if user and user.password == password:
            self.send_response(302)
            c = cookies.SimpleCookie()
            c["user"] = username
            c["user"]["path"] = "/"
            self.send_header('Set-Cookie', c.output(header='').strip())
            if user.is_admin:
                self.send_header('Location', '/admin')
            else:
                self.send_header('Location', '/dashboard')
            self.end_headers()
        else:
            self.send_error(401, "Invalid Credentials")

    def handle_register(self, params):
        username = params.get("username", [""])[0]
        password = params.get("password", [""])[0]
        
        if DATA_MGR.get_user(username):
             self.send_error(400, "User already exists")
             return
             
        new_user = User(username, password)
        DATA_MGR.add_user(new_user)
        save_data(DATA_MGR)
        
        # Auto login
        self.send_response(302)
        c = cookies.SimpleCookie()
        c["user"] = username
        c["user"]["path"] = "/"
        self.send_header('Set-Cookie', c.output(header='').strip())
        self.send_header('Location', '/dashboard')
        self.end_headers()

    def handle_dashboard(self):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        
        stats_html = f"""
            <div class="stats-card">
                <h3>My Stats</h3>
                <div class="flex" style="justify-content: space-between; margin-top: 1rem;">
                    <div>
                        <div class="text-sm">Coupons Given</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--success);">{user.coupons_given}</div>
                    </div>
                    <div>
                        <div class="text-sm">Coupons Taken</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--secondary);">{user.coupons_taken}</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-card" style="margin-top: 1rem;">
                <h3 style="color: var(--danger);">⚠️ Soon to Expire</h3>
                <ul style="list-style: none; margin-top: 1rem;">
                    {self._render_soon_expiring()}
                </ul>
            </div>
        """
        
        # We need to inject this into user_dashboard.html
        # Since my replace logic is simple, I'll pass the whole block
        self.serve_template("user_dashboard.html", {
            "username": user.username,
            "sidebar_content": stats_html
        })

    def handle_give_page(self):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        self.serve_template("give_coupon.html", {"username": user.username})

    def handle_add_coupon(self, params):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        
        category = params.get("category", [""])[0]
        brand = params.get("brand", [""])[0]
        offer = params.get("offer", [""])[0]
        code = params.get("code", [""])[0]
        expiry = params.get("expiry", [""])[0]
        
        new_coupon = Coupon(
            id=str(uuid.uuid4())[:8],
            owner_username=user.username,
            category=category,
            brand=brand,
            offer_amount=offer,
            expiry_date=expiry,
            code=code
        )
        
        DATA_MGR.add_coupon(new_coupon)
        user.coupons_given += 1
        user.given_history.append(new_coupon.id)
        save_data(DATA_MGR)
        
        self.redirect("/dashboard")

    def handle_take_page(self, query):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        
        category_filter = query.get("category", ["Food"])[0]
        coupons = DATA_MGR.get_coupons_by_category(category_filter)
        
        # Render coupons grid
        coupons_html = ""
        for c in coupons:
            if c.owner_username == user.username: continue # Skip own
            
            coupons_html += f"""
            <div class="coupon-card cat-{c.category}">
                <span class="tag">{c.category}</span>
                <h3>{c.brand}</h3>
                <p style="font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;">{c.offer_amount}</p>
                <p class="text-sm">Expires: {c.expiry_date}</p>
                <p class="text-sm">From: {c.owner_username}</p>
                <form action="/claim_coupon" method="POST" style="margin-top: 1rem;">
                    <input type="hidden" name="coupon_id" value="{c.id}">
                    <button type="submit" class="btn" style="width: 100%;">Claim It</button>
                </form>
            </div>
            """
            
        if not coupons_html:
            coupons_html = "<p>No coupons available in this category.</p>"
            
        error_msg = ""
        if not user.can_take_coupon():
            error_msg = f"""
            <div class="alert">
                You cannot claim more coupons! You have given {user.coupons_given} but taken {user.coupons_taken}. 
                <br>Rule: You must give as many as you take.
            </div>
            """

        self.serve_template("take_coupon.html", {
            "username": user.username,
            "coupons_grid": coupons_html,
            "current_category": category_filter,
            "alert": error_msg
        })

    def handle_claim_coupon(self, params):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        
        coupon_id = params.get("coupon_id", [""])[0]
        
        success = DATA_MGR.exchange_coupon(user.username, coupon_id)
        save_data(DATA_MGR)
        
        if success:
            self.redirect("/dashboard")
        else:
            # Should show error, but simple redirect for now
            self.redirect("/take?error=failed")

    def handle_logout(self):
        self.send_response(302)
        c = cookies.SimpleCookie()
        c["user"] = ""
        c["user"]["expires"] = 0
        self.send_header('Set-Cookie', c.output(header='').strip())
        self.send_header('Location', '/login')
        self.end_headers()

    def handle_admin_dashboard(self):
        user = self.get_session_user()
        if not user or not user.is_admin: return self.redirect("/login")
        
        # Render User Table
        users_html = ""
        for u in DATA_MGR.users.values():
            if u.is_admin: continue
            users_html += f"""
            <tr>
                <td>{u.username}</td>
                <td>{u.coupons_given}</td>
                <td>{u.coupons_taken}</td>
                <td>
                     <form action="/admin/delete_user" method="POST" onsubmit="return confirm('Delete user?');">
                        <input type="hidden" name="username" value="{u.username}">
                        <button class="btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; border-color: red; color: red;">Remove</button>
                    </form>
                </td>
            </tr>
            """
            
        # Render Coupons Table
        coupons_html = ""
        for c in DATA_MGR.get_all_coupons():
            coupons_html += f"""
            <tr>
                <td>{c.brand}</td>
                <td>{c.offer_amount}</td>
                <td>{c.owner_username}</td>
                <td><span class="tag">{c.status}</span></td>
                <td>
                    <form action="/admin/delete_coupon" method="POST">
                        <input type="hidden" name="coupon_id" value="{c.id}">
                        <button class="btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; border-color: red; color: red;">Del</button>
                    </form>
                </td>
            </tr>
            """
            
        self.serve_template("admin_dashboard.html", {
            "users_rows": users_html,
            "coupons_rows": coupons_html,
            "recent_activity": self._render_activity()
        })

    def handle_admin_delete_user(self, params):
        u_name = params.get("username", [""])[0]
        if u_name in DATA_MGR.users:
            del DATA_MGR.users[u_name]
            save_data(DATA_MGR)
        self.redirect("/admin")

    def handle_admin_delete_coupon(self, params):
        c_id = params.get("coupon_id", [""])[0]
        if c_id in DATA_MGR.coupons:
            del DATA_MGR.coupons[c_id]
            # Warning: this leaves it in category lists/heap, but they check existence safely usually. 
            # Ideally cleanup fully but constraints say "Remove Coupons Manually" is a feature.
            save_data(DATA_MGR)
        self.redirect("/admin")

    def handle_my_coupons(self):
        user = self.get_session_user()
        if not user: return self.redirect("/login")
        
        rows = ""
        count = 0
        for c_id in user.taken_history:
            coupon = DATA_MGR.coupons.get(c_id)
            if coupon:
                rows += f"""
                <tr>
                    <td>{coupon.brand}</td>
                    <td><span class="tag">{coupon.category}</span></td>
                    <td>{coupon.offer_amount}</td>
                    <td><span class="code-block">{coupon.code}</span></td>
                    <td>{coupon.expiry_date}</td>
                    <td>{coupon.owner_username}</td>
                </tr>
                """
                count += 1
                
        msg = ""
        if count == 0:
            msg = "<p style='padding: 1rem; text-align: center; color: var(--text-muted);'>You haven't claimed any coupons yet.</p>"

        self.serve_template("my_coupons.html", {
            "coupons_rows": rows,
            "no_coupons_msg": msg
        })

    # --- Render Helpers ---
    def _render_soon_expiring(self):
        soon = DATA_MGR.get_soon_to_expire()
        if not soon: return "<li>No expiring coupons</li>"
        html = ""
        for c in soon:
            html += f"<li style='margin-bottom:0.5rem; font-size:0.9rem;'><strong>{c.brand}</strong> <span style='color:red;'>{c.expiry_date}</span></li>"
        return html

    def _render_activity(self):
        html = "<ul style='padding-left: 1rem;'>"
        for act in DATA_MGR.recent_activity:
            html += f"<li style='margin-bottom: 0.5rem;'>{act}</li>"
        html += "</ul>"
        return html

if __name__ == "__main__":
    print(f"Starting CouponX on port {PORT}...")
    with socketserver.TCPServer(("", PORT), CouponXHandler) as httpd:
        httpd.serve_forever()
