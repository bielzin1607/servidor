from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)

# Caminho para o banco de dados SQLite
db_path = r"\\192.168.1.192\arquivos\Acervo\documentos.db"

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return conn

# Rota para consultar protocolos por sequencia_caixa, número de documento e apresentante
@app.route('/consultar_documentos', methods=['GET'])
def consultar_protocolos():
    sequencia_caixa = request.args.get('sequencia_caixa')
    numero_documento = request.args.get('numero_documento')
    apresentante = request.args.get('apresentante')
    pagina = int(request.args.get('pagina', 1))
    offset = (pagina - 1) * 25
    
    if not sequencia_caixa:
        return jsonify({'error': 'Sequência da caixa não fornecida.'}), 400

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Monta a query e os parâmetros dinamicamente
        query = '''SELECT numero_documento, apresentante, natureza, status, data_cadastro 
                   FROM documentos 
                   WHERE sequencia_caixa = ?'''
        params = [sequencia_caixa]

        # Adiciona a condição do número do documento se for fornecido
        if numero_documento:
            query += ' AND numero_documento = ?'
            params.append(numero_documento)

        # Adiciona a condição do apresentante se for fornecido
        if apresentante:
            query += ' AND apresentante LIKE ?'
            params.append(f"%{apresentante}%")

        # Limite e deslocamento para paginação
        query += ' LIMIT 25 OFFSET ?'
        params.append(offset)

        # Executa a consulta
        c.execute(query, params)
        documentos = c.fetchall()

        # Calcula o total de páginas
        c.execute('''SELECT COUNT(*) FROM documentos 
                     WHERE sequencia_caixa = ?''' + 
                     (' AND numero_documento = ?' if numero_documento else '') +
                     (' AND apresentante LIKE ?' if apresentante else ''), 
                     params[:-1])  # Exclui o offset para contar o total de resultados
        total_count = c.fetchone()[0]
        total_pages = (total_count // 25) + (1 if total_count % 25 > 0 else 0)

        conn.close()

        # Gera a lista de documentos
        documentos_list = [
            {
                'numero_documento': documento['numero_documento'],
                'apresentante': documento['apresentante'],
                'natureza': documento['natureza'],
                'status': documento['status'],
                'data_cadastro': documento['data_cadastro']
            } for documento in documentos 
        ]

        return render_template('protocolos.html', 
                               sequencia_caixa=sequencia_caixa, 
                               documentos=documentos_list, 
                               pagina_atual=pagina,
                               total_pages=total_pages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


