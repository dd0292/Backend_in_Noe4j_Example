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
        get_all_usuarios  # We'll need to add this function to main.py
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
        self.root.geometry("800x600")
        
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
        main_frame.rowconfigure(1, weight=1)
        
        # User selection
        ttk.Label(main_frame, text="Select User:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_combo = ttk.Combobox(main_frame, textvariable=self.current_user, state="readonly")
        self.user_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.user_combo.bind('<<ComboboxSelected>>', self.on_user_selected)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(buttons_frame, text="View Global Posts", 
                  command=self.view_global_posts).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="View My Posts", 
                  command=self.view_my_posts).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Common Friends", 
                  command=self.view_common_friends).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Friend Suggestions", 
                  command=self.view_friend_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Create Post", 
                  command=self.create_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Add Friend", 
                  command=self.add_friend).pack(side=tk.LEFT, padx=5)
        
        # Results area
        self.results_text = tk.Text(main_frame, height=20, width=80)
        self.results_text.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=10)
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


class PostDialog:
    """Dialog for creating a new post"""
    def __init__(self, parent, user_email):
        self.top = tk.Toplevel(parent)
        self.top.title(f"Create Post - {user_email}")
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
        ttk.Button(self.top, text="Create", command=self.ok).grid(row=4, column=1, padx=5, pady=10)
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


def main():
    root = tk.Tk()
    app = SocialApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()