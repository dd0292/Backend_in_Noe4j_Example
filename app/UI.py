import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Dict, Any
import sys
import os

# Import functions from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from main import (
        get_driver, upsert_usuario, create_publicacion, create_amistad,
        publicaciones_por_usuario, amigos_en_comun, top_publicaciones,
        sugerencias_de_amigos, UsuarioInput, PublicacionInput,
        get_all_usuarios, delete_all  # We'll need to add this function to main.py
    )
except ImportError:
    # Fallback implementations for demonstration
    def get_driver():
        return None
    
    def upsert_usuario(driver, user):
        print(f"Creating user: {user.nombre}")
    
    def create_publicacion(driver, email, pub):
        print(f"Creating post for {email}: {pub.contenido}")
    
    def create_amistad(driver, email_a, email_b):
        print(f"Creating friendship between {email_a} and {email_b}")
    
    def publicaciones_por_usuario(driver, email):
        return [{"id": "1", "contenido": "Sample post", "fecha": "2025-01-01", "likes": 5, "etiquetas": ["sample"]}]
    
    def amigos_en_comun(driver, email1, email2):
        return ["Common Friend 1", "Common Friend 2"]
    
    def top_publicaciones(driver, limit=5):
        return [{"id": "1", "autor": "Sample User", "contenido": "Top post", "likes": 10}]
    
    def sugerencias_de_amigos(driver, email):
        return ["Suggested Friend 1", "Suggested Friend 2"]
    
    def get_all_usuarios(driver):
        return ["ana@mail.com", "bruno@mail.com", "carla@mail.com", "diego@mail.com", "elena@mail.com"]
    
    def delete_all(driver):
        print("Deleting all data")
    
    class UsuarioInput:
        def __init__(self, id, nombre, email, fechaRegistro):
            self.id = id
            self.nombre = nombre
            self.email = email
            self.fechaRegistro = fechaRegistro
    
    class PublicacionInput:
        def __init__(self, contenido, fecha, likes, etiquetas):
            self.contenido = contenido
            self.fecha = fecha
            self.likes = likes
            self.etiquetas = etiquetas

class SocialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Network App")
        self.root.geometry("900x700")
        
        # Initialize database connection
        try:
            self.driver = get_driver()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not connect to database: {e}")
            self.driver = None
        
        # Current user
        self.current_user = tk.StringVar()
        
        # Create UI
        self.create_widgets()
        
        # Load initial data
        self.refresh_users()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # User selection
        ttk.Label(main_frame, text="Select User:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_combo = ttk.Combobox(main_frame, textvariable=self.current_user, state="readonly")
        self.user_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.user_combo.bind('<<ComboboxSelected>>', self.on_user_selected)
        
        # Social Features Buttons frame
        social_frame = ttk.LabelFrame(main_frame, text="Social Features", padding="5")
        social_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(social_frame, text="View Global Posts", 
                  command=self.view_global_posts).pack(side=tk.LEFT, padx=5)
        ttk.Button(social_frame, text="View My Posts", 
                  command=self.view_my_posts).pack(side=tk.LEFT, padx=5)
        ttk.Button(social_frame, text="Common Friends", 
                  command=self.view_common_friends).pack(side=tk.LEFT, padx=5)
        ttk.Button(social_frame, text="Friend Suggestions", 
                  command=self.view_friend_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(social_frame, text="Create Post", 
                  command=self.create_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(social_frame, text="Add Friend", 
                  command=self.add_friend).pack(side=tk.LEFT, padx=5)
        
        # CRUD Operations Buttons frame
        crud_frame = ttk.LabelFrame(main_frame, text="CRUD Operations", padding="5")
        crud_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # User CRUD buttons
        ttk.Button(crud_frame, text="Create User", 
                  command=self.create_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(crud_frame, text="List Users", 
                  command=self.list_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(crud_frame, text="Search Users", 
                  command=self.search_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(crud_frame, text="Update User", 
                  command=self.update_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(crud_frame, text="Delete User", 
                  command=self.delete_user).pack(side=tk.LEFT, padx=2)
        
        # Post CRUD buttons
        ttk.Button(crud_frame, text="Update Post", 
                  command=self.update_post).pack(side=tk.LEFT, padx=2)
        ttk.Button(crud_frame, text="Delete Post", 
                  command=self.delete_post).pack(side=tk.LEFT, padx=2)
        
        # Results area
        self.results_text = tk.Text(main_frame, height=25, width=100)
        self.results_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=3, column=2, sticky=(tk.N, tk.S), pady=10)
        self.results_text.configure(yscrollcommand=scrollbar.set)
    
    def refresh_users(self):
        """Refresh the list of users in the combobox"""
        if not self.driver:
            # Demo data
            users = ["ana@mail.com", "bruno@mail.com", "carla@mail.com", "diego@mail.com", "elena@mail.com"]
            self.user_combo['values'] = users
            if users:
                self.current_user.set(users[0])
            return
        
        try:
            # This function would need to be added to main.py
            # For now, we'll use a direct query
            with self.driver.session() as session:
                result = session.run("MATCH (u:Usuario) RETURN u.email AS email")
                users = [record["email"] for record in result]
                self.user_combo['values'] = users
                if users:
                    self.current_user.set(users[0])
        except Exception as e:
            messagebox.showerror("Error", f"Could not load users: {e}")
    
    def on_user_selected(self, event):
        """Handle user selection change"""
        self.clear_results()
        self.results_text.insert(tk.END, f"Selected user: {self.current_user.get()}\n")
    
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)
    
    # =========================================================================
    # SOCIAL FEATURES (existing functions)
    # =========================================================================
    
    def view_global_posts(self):
        """Display global posts"""
        if not self.driver:
            # Demo data
            posts = top_publicaciones(None)
        else:
            posts = top_publicaciones(self.driver)
        
        self.clear_results()
        self.results_text.insert(tk.END, "=== GLOBAL POSTS ===\n\n")
        
        for post in posts:
            self.results_text.insert(tk.END, f"Author: {post.get('autor', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"Content: {post.get('contenido', 'No content')}\n")
            self.results_text.insert(tk.END, f"Likes: {post.get('likes', 0)}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n\n")
    
    def view_my_posts(self):
        """Display current user's posts"""
        user_email = self.current_user.get()
        if not user_email:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        if not self.driver:
            # Demo data
            posts = publicaciones_por_usuario(None, user_email)
        else:
            posts = publicaciones_por_usuario(self.driver, user_email)
        
        self.clear_results()
        self.results_text.insert(tk.END, f"=== {user_email}'s POSTS ===\n\n")
        
        for post in posts:
            self.results_text.insert(tk.END, f"ID: {post.get('id', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"Date: {post.get('fecha', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"Content: {post.get('contenido', 'No content')}\n")
            self.results_text.insert(tk.END, f"Likes: {post.get('likes', 0)}\n")
            tags = post.get('etiquetas', [])
            self.results_text.insert(tk.END, f"Tags: {', '.join(tags) if tags else 'None'}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n\n")
    
    def view_common_friends(self):
        """Display common friends with another user"""
        user_email = self.current_user.get()
        if not user_email:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        # Get another user to compare with
        other_user = simpledialog.askstring(
            "Common Friends", 
            "Enter the email of another user to find common friends:",
            initialvalue=""
        )
        
        if not other_user:
            return
        
        if not self.driver:
            # Demo data
            common_friends = amigos_en_comun(None, user_email, other_user)
        else:
            common_friends = amigos_en_comun(self.driver, user_email, other_user)
        
        self.clear_results()
        self.results_text.insert(tk.END, f"=== COMMON FRIENDS BETWEEN {user_email} AND {other_user} ===\n\n")
        
        if common_friends:
            for friend in common_friends:
                self.results_text.insert(tk.END, f"• {friend}\n")
        else:
            self.results_text.insert(tk.END, "No common friends found.\n")
    
    def view_friend_suggestions(self):
        """Display friend suggestions for current user"""
        user_email = self.current_user.get()
        if not user_email:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        if not self.driver:
            # Demo data
            suggestions = sugerencias_de_amigos(None, user_email)
        else:
            suggestions = sugerencias_de_amigos(self.driver, user_email)
        
        self.clear_results()
        self.results_text.insert(tk.END, f"=== FRIEND SUGGESTIONS FOR {user_email} ===\n\n")
        
        if suggestions:
            for suggestion in suggestions:
                self.results_text.insert(tk.END, f"• {suggestion}\n")
        else:
            self.results_text.insert(tk.END, "No friend suggestions available.\n")
    
    def create_post(self):
        """Create a new post for the current user"""
        user_email = self.current_user.get()
        if not user_email:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        # Create a dialog for post input
        dialog = PostDialog(self.root, user_email)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            contenido, fecha, likes, etiquetas = dialog.result
            
            # Create post input object
            post_input = PublicacionInput(
                contenido=contenido,
                fecha=fecha,
                likes=likes,
                etiquetas=etiquetas
            )
            
            # Create the post
            if self.driver:
                create_publicacion(self.driver, user_email, post_input)
            else:
                create_publicacion(None, user_email, post_input)
            
            messagebox.showinfo("Success", "Post created successfully!")
            self.view_my_posts()  # Refresh to show the new post
    
    def add_friend(self):
        """Add a friend for the current user"""
        user_email = self.current_user.get()
        if not user_email:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        # Get friend's email
        friend_email = simpledialog.askstring(
            "Add Friend", 
            "Enter the email of the user you want to add as a friend:",
            initialvalue=""
        )
        
        if not friend_email:
            return
        
        if friend_email == user_email:
            messagebox.showwarning("Warning", "You cannot add yourself as a friend")
            return
        
        # Create the friendship
        if self.driver:
            create_amistad(self.driver, user_email, friend_email)
        else:
            create_amistad(None, user_email, friend_email)
        
        messagebox.showinfo("Success", f"Friend request sent to {friend_email}!")
        self.view_friend_suggestions()  # Refresh suggestions
    
    # =========================================================================
    # CRUD OPERATIONS (new functions)
    # =========================================================================
    
    def create_user(self):
        """Create a new user"""
        dialog = UserDialog(self.root, "Create User")
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            id, nombre, email, fechaRegistro = dialog.result
            
            # Create user input object
            user_input = UsuarioInput(
                id=id,
                nombre=nombre,
                email=email,
                fechaRegistro=fechaRegistro
            )
            
            # Create the user
            if self.driver:
                upsert_usuario(self.driver, user_input)
            else:
                upsert_usuario(None, user_input)
            
            messagebox.showinfo("Success", "User created successfully!")
            self.refresh_users()  # Refresh the user list
    
    def list_users(self):
        """List all users"""
        if not self.driver:
            # Demo data
            users = get_all_usuarios(None)
        else:
            users = get_all_usuarios(self.driver)
        
        self.clear_results()
        self.results_text.insert(tk.END, "=== ALL USERS ===\n\n")
        
        if users:
            for user in users:
                self.results_text.insert(tk.END, f"• {user}\n")
        else:
            self.results_text.insert(tk.END, "No users found.\n")
    
    def search_users(self):
        """Search for users by name or email"""
        search_term = simpledialog.askstring(
            "Search Users", 
            "Enter name or email to search:",
            initialvalue=""
        )
        
        if not search_term:
            return
        
        if not self.driver:
            # Demo data
            users = get_all_usuarios(None)
            filtered_users = [user for user in users if search_term.lower() in user.lower()]
        else:
            # This query would need to be implemented in main.py
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (u:Usuario) WHERE u.nombre CONTAINS $search OR u.email CONTAINS $search RETURN u.email AS email",
                    search=search_term
                )
                filtered_users = [record["email"] for record in result]
        
        self.clear_results()
        self.results_text.insert(tk.END, f"=== SEARCH RESULTS FOR '{search_term}' ===\n\n")
        
        if filtered_users:
            for user in filtered_users:
                self.results_text.insert(tk.END, f"• {user}\n")
        else:
            self.results_text.insert(tk.END, "No users found matching your search.\n")
    
    def update_user(self):
        """Update an existing user"""
        user_email = simpledialog.askstring(
            "Update User", 
            "Enter the email of the user to update:",
            initialvalue=self.current_user.get()
        )
        
        if not user_email:
            return
        
        # In a real implementation, you would fetch the current user data here
        # For now, we'll create a dialog with placeholder values
        dialog = UserDialog(self.root, "Update User", user_email)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            id, nombre, email, fechaRegistro = dialog.result
            
            # Create user input object
            user_input = UsuarioInput(
                id=id,
                nombre=nombre,
                email=email,
                fechaRegistro=fechaRegistro
            )
            
            # Update the user
            if self.driver:
                upsert_usuario(self.driver, user_input)
            else:
                upsert_usuario(None, user_input)
            
            messagebox.showinfo("Success", "User updated successfully!")
            self.refresh_users()  # Refresh the user list
    
    def delete_user(self):
        """Delete a user"""
        user_email = simpledialog.askstring(
            "Delete User", 
            "Enter the email of the user to delete:",
            initialvalue=""
        )
        
        if not user_email:
            return
        
        if user_email == self.current_user.get():
            messagebox.showwarning("Warning", "You cannot delete the currently selected user")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete user {user_email}? This action cannot be undone."
        )
        
        if not confirm:
            return
        
        # Delete the user
        # This function would need to be implemented in main.py
        if self.driver:
            with self.driver.session() as session:
                session.run("MATCH (u:Usuario {email: $email}) DETACH DELETE u", email=user_email)
        else:
            print(f"Deleting user: {user_email}")
        
        messagebox.showinfo("Success", "User deleted successfully!")
        self.refresh_users()  # Refresh the user list
    
    def update_post(self):
        """Update an existing post"""
        post_id = simpledialog.askstring(
            "Update Post", 
            "Enter the ID of the post to update:",
            initialvalue=""
        )
        
        if not post_id:
            return
        
        # In a real implementation, you would fetch the current post data here
        # For now, we'll create a dialog with placeholder values
        dialog = PostDialog(self.root, "Update Post")
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            contenido, fecha, likes, etiquetas = dialog.result
            
            # Update the post
            # This function would need to be implemented in main.py
            if self.driver:
                with self.driver.session() as session:
                    session.run(
                        "MATCH (p:Publicación {id: $id}) SET p.contenido = $contenido, p.fecha = date($fecha), p.likes = $likes",
                        id=post_id, contenido=contenido, fecha=fecha, likes=likes
                    )
            else:
                print(f"Updating post {post_id}: {contenido}")
            
            messagebox.showinfo("Success", "Post updated successfully!")
            self.view_my_posts()  # Refresh to show the updated post
    
    def delete_post(self):
        """Delete a post"""
        post_id = simpledialog.askstring(
            "Delete Post", 
            "Enter the ID of the post to delete:",
            initialvalue=""
        )
        
        if not post_id:
            return
        
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete post {post_id}? This action cannot be undone."
        )
        
        if not confirm:
            return
        
        # Delete the post
        # This function would need to be implemented in main.py
        if self.driver:
            with self.driver.session() as session:
                session.run("MATCH (p:Publicación {id: $id}) DETACH DELETE p", id=post_id)
        else:
            print(f"Deleting post: {post_id}")
        
        messagebox.showinfo("Success", "Post deleted successfully!")
        self.view_my_posts()  # Refresh to show the updated list


class PostDialog:
    """Dialog for creating or updating a post"""
    def __init__(self, parent, user_email, mode="create"):
        self.top = tk.Toplevel(parent)
        self.top.title(f"{mode.title()} Post - {user_email}")
        self.top.geometry("400x300")
        self.result = None
        
        # Content
        ttk.Label(self.top, text="Content:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.content_text = tk.Text(self.top, height=5, width=40)
        self.content_text.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Date
        ttk.Label(self.top, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_entry = ttk.Entry(self.top)
        self.date_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.date_entry.insert(0, "2025-02-10")  # Default date
        
        # Likes
        ttk.Label(self.top, text="Likes:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.likes_spinbox = ttk.Spinbox(self.top, from_=0, to=1000, width=10)
        self.likes_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.likes_spinbox.set("0")
        
        # Tags
        ttk.Label(self.top, text="Tags (comma separated):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.tags_entry = ttk.Entry(self.top)
        self.tags_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.tags_entry.insert(0, "general")
        
        # Buttons
        ttk.Button(self.top, text="OK", command=self.ok).grid(row=4, column=1, padx=5, pady=10)
        ttk.Button(self.top, text="Cancel", command=self.cancel).grid(row=4, column=2, padx=5, pady=10)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        """Handle OK button click"""
        contenido = self.content_text.get(1.0, tk.END).strip()
        fecha = self.date_entry.get().strip()
        likes = int(self.likes_spinbox.get())
        etiquetas = [tag.strip() for tag in self.tags_entry.get().split(",")]
        
        if not contenido:
            messagebox.showwarning("Warning", "Content cannot be empty")
            return
        
        self.result = (contenido, fecha, likes, etiquetas)
        self.top.destroy()
    
    def cancel(self):
        """Handle Cancel button click"""
        self.top.destroy()


class UserDialog:
    """Dialog for creating or updating a user"""
    def __init__(self, parent, title, email=None):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("400x250")
        self.result = None
        
        # ID
        ttk.Label(self.top, text="User ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.id_entry = ttk.Entry(self.top)
        self.id_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.id_entry.insert(0, f"U{str(hash(email))[-4:]}" if email else "U001")
        
        # Name
        ttk.Label(self.top, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(self.top)
        self.name_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.name_entry.insert(0, "")
        
        # Email
        ttk.Label(self.top, text="Email:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_entry = ttk.Entry(self.top)
        self.email_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        if email:
            self.email_entry.insert(0, email)
            self.email_entry.config(state="readonly")
        
        # Registration Date
        ttk.Label(self.top, text="Registration Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.date_entry = ttk.Entry(self.top)
        self.date_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.date_entry.insert(0, "2025-02-10")  # Default date
        
        # Buttons
        ttk.Button(self.top, text="OK", command=self.ok).grid(row=4, column=1, padx=5, pady=10)
        ttk.Button(self.top, text="Cancel", command=self.cancel).grid(row=4, column=2, padx=5, pady=10)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        """Handle OK button click"""
        id = self.id_entry.get().strip()
        nombre = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        fechaRegistro = self.date_entry.get().strip()
        
        if not all([id, nombre, email, fechaRegistro]):
            messagebox.showwarning("Warning", "All fields are required")
            return
        
        self.result = (id, nombre, email, fechaRegistro)
        self.top.destroy()
    
    def cancel(self):
        """Handle Cancel button click"""
        self.top.destroy()


def main():
    root = tk.Tk()
    app = SocialApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()