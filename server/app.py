from flask import Flask, request, jsonify, render_template, abort
from flask_bcrypt import Bcrypt

from flask_cors import CORS
from werkzeug.utils import secure_filename
import mysql.connector 

import os
import time

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
class Conector:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()

        self.bcrypt = Bcrypt(app)

        

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            print(f"Error de conexión a la base de datos: {err}")
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err


        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuario (
                idUsuario INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(255) NOT NULL,
                ciudad VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                contrasena VARCHAR(255) NOT NULL
            )
        ''')
        self.conn.commit()

        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)


     #Metodo para agregar un Usuario.
    def agregar_usuario(self, nombre, ciudad, email, contrasena):

        self.cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        usuario_existe = self.cursor.fetchone()
        if usuario_existe:
            return False
        contrasena_hasheada = self.hash_password(contrasena)
        sql = "INSERT INTO usuario (nombre, ciudad, email, contrasena) VALUES (%s, %s, %s, %s)"
        valores=(nombre, ciudad, email, contrasena_hasheada)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return True


    #Metodo para autenticar Usuario.
    def autenticar_usuario(self, email, contrasena):
        self.cursor.execute("SELECT * FROM usuario WHERE email = %s AND contrasena = %s", (email, contrasena,))
        usuario = self.cursor.fetchone()
        return usuario


    #Metodo para consultar un Usuario por su Id.
    def consultar_usuario(self, email):
        self.cursor.execute("SELECT * FROM usuario WHERE email = %s" , (email,))
        return self.cursor.fetchone()


    # Metodo para mostrar un Usuario
    def mostrar_usuario(self, email):
        # Mostramos los datos de un Usuario a partir de su Email
        usuario = self.consultar_usuario(email)
        if usuario:
            print("-" * 40)
            print(f"Nombre del Usuario: {usuario['nombre']}")
            print(f"Ciudad del Usuario: {usuario['ciudad']}")
            print(f"Email del Usuario: {usuario['email']}")
            print(f"Contraseña del Usuario: {usuario['contrasena']}")
            print("-" * 40)
        else:
            print("Usuario no encontrado.")

    

    #Metodo para listar Usuarios
    def listar_usuarios(self):
        self.cursor.execute("SELECT * FROM usuario")
        usuarios = self.cursor.fetchall()
        return usuarios



    # Metodo para encryptar password
    def hash_password(self, password):
        return self.bcrypt.generate_password_hash(password).decode('utf-8')
   
    


    #Metodo para modificar un Usuario.
    def modificar_usuario(self, email, nuevo_nombre, nueva_ciudad, nuevo_email, nueva_contrasena):
        sql = "UPDATE usuario SET nombre= %s, ciudad= %s, email= %s, contrasena= %s WHERE email= %s"  
        contrasena_hasheada = self.hash_password(nueva_contrasena)
        valores = (nuevo_nombre, nueva_ciudad, nuevo_email, contrasena_hasheada, email)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0



    # Metodo para eliminar un Usuario
    def eliminar_usuario(self, email):

        self.cursor.execute("DELETE FROM usuario WHERE email = %s", (email,))
        self.conn.commit()
        return self.cursor.rowcount > 0










#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
# Creamos una instancia de Conector
#conexion = Conector(host='localhost', user='root', password='root', database='cryptoMercado')  
conexion = Conector(host='ayacodoacodo.mysql.pythonanywhere-services.com', user='ayacodoacodo', password='Error2023', database='ayacodoacodo$cryptoMercado')  






    
# Endpoint para listar Usuarios
@app.route("/usuario", methods=["GET"])
def listar_usuarios():
    usuarios = conexion.listar_usuarios()
    return jsonify(usuarios)


# Endpoint para mostrar un Usuario por su email
@app.route("/usuario/<string:email>", methods=["GET"])
def mostrar_usuario(email):
    usuario = conexion.consultar_usuario(email)
    if usuario:
        return jsonify(usuario)
    else:
        abort(404, description="Usuario no encontrado")



# Endpoint para crear un nuevo Usuario
@app.route("/usuario", methods=["POST"])
def nuevo_usuario():
    # Levanta los datos del formulario
    nombre = request.form['nombre']
    ciudad = request.form['ciudad']
    email = request.form['email']
    contrasena = request.form['contrasena']
    confirmarContrasena = request.form['confirmarContrasena']
    

    if contrasena != confirmarContrasena:
        return jsonify({"mensaje": "Las contraseñas no coinciden"}), 400

    if conexion.agregar_usuario(nombre, ciudad, email, contrasena):
        return jsonify({"mensaje": "Usuario agregado"}), 201
    else:
        return jsonify({"mensaje": "Usuario ya existente"}), 400

    


# Endpoint para el inicio de sesión
@app.route("/login", methods=["POST"])
def login():
    # Levanta los datos del formulario
    email = request.form.get('email')
    contrasena = request.form.get('contrasena')

    # Utilizar el método de autenticación de la clase Conector
    usuario = conexion.autenticar_usuario(email, contrasena)

    if usuario:
        return jsonify({'mensaje': 'Inicio de sesión exitoso'})
    else:
        return jsonify({'mensaje': 'Credenciales incorrectas'}), 401



# Endpoint para modificar un Usuario por el email
@app.route("/usuario/<string:email>", methods=["PUT"])
def modificar_usuario(email):
    # Recojo los datos del Formulario
    nuevo_nombre = request.form.get("nombre")
    nueva_ciudad = request.form.get("ciudad")
    nuevo_email = request.form.get("email")
    nueva_contrasena = request.form.get("contrasena")

    # Actualizando Usuario
    if conexion.modificar_usuario(email, nuevo_nombre, nueva_ciudad, nuevo_email, nueva_contrasena):
        return jsonify({"mensaje": "Se ha actualizado correctamente el usuario."}), 200
    else:
        return jsonify({"mensaje": "No se pudo actualizar el usuario"}), 404


# Endpoint para eliminar un Usuario
@app.route("/usuario/<string:email>", methods=["DELETE"])
def eliminar_usuario(email):
    
    if conexion.eliminar_usuario(email):
        return jsonify({"mensaje": "Usuario eliminado"}), 200
    else:
        return jsonify({"mensaje": "Error al eliminar el usuario"}), 500
   


if __name__ == '__main__':
    app.run(debug=True)