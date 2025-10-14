# main.py
from database import get_driver, delete_all, init_schema, seed_data, get_database_info
from database import top_publicaciones, publicaciones_por_usuario, amigos_en_comun, sugerencias_de_amigos, publicacion_to_str
import UI
import tkinter as tk

def initialize_database():
    """Initialize database with example data"""
    print(f"Inicializando base de datos...")
    
    with get_driver() as driver:
        print(" Conexión establecida")
        
        print("  Eliminando datos previos...")
        delete_all(driver)
        
        print(" Creando constraints...")
        init_schema(driver)
        
        print(" Sembrando datos...")
        seed_data(driver)
        
        # Data verification
        print("\n" + "="*50)
        print("VERIFICACIÓN DE DATOS")
        print("="*50)
        
        info = get_database_info(driver)
        print(f"✓ Usuarios en BD: {info['usuarios']}")
        print(f"✓ Publicaciones en BD: {info['publicaciones']}")
        print(f"✓ Etiquetas únicas en BD: {info['etiquetas']}")
        print(f"✓ Etiquetas: {', '.join(info['lista_etiquetas'])}")
        
        print("\nAmistades por usuario (top 5):")
        for nombre, count in info['top_amistades']:
            print(f"  {nombre}: {count} amigos")
        
        print("\n" + "="*50)
        print("DEMOSTRACIÓN DE CONSULTAS")
        print("="*50)
        
        print("\nTop 5 publicaciones:")
        for row in top_publicaciones(driver, 5):
            print(publicacion_to_str(row))
        
        print("\nPublicaciones de Ana:")
        for row in publicaciones_por_usuario(driver, "ana@mail.com"):
            print(publicacion_to_str(row))
        
        print("\nAmigos en común entre Ana y Bruno:")
        print(amigos_en_comun(driver, "ana@mail.com", "bruno@mail.com"))
        
        print("\nSugerencias de amigos para Ana:")
        print(sugerencias_de_amigos(driver, "ana@mail.com"))
        
        print("\n🎉 Inicialización completada!")

def main():
    """Principal function that initializes the DB and launch the UI"""
    try:
        # Initialize the database
        initialize_database()
        
        # Launch the UI
        print("\n" + "="*50)
        print("LANZANDO INTERFAZ GRÁFICA")
        print("="*50)
        
        root = tk.Tk()
        app = UI.SocialApp(root)
        root.mainloop()
        
    except Exception as e:
        print(f" Error: {e}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
