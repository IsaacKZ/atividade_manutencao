from database import conectar

def login(username, senha): # USUARIO: admin    
    conexao = conectar()    # SENHA:   admin123
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id FROM usuarios WHERE username = ? AND senha = ?",
        (username, senha),
    )
    usuario = cursor.fetchone()
    conexao.close()
    return usuario is not None