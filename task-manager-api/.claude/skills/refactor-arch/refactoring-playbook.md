# Refactoring Playbook

Playbooks passo-a-passo com transformações antes/depois detalhadas para resolver cada anti-pattern.

---

## Playbook #1: Eliminar SQL Injection

### Problema
Queries construídas por concatenação de strings permitem injeção SQL.

### Impacto
- 🔴 CRÍTICO: Acesso não autorizado, perda de dados

### Exemplo Antes

**File:** `models.py` (Python/SQLite)

```python
def get_produto_por_id(id):
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    return cursor.fetchone()

def criar_produto(nome, descricao, preco):
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco) VALUES ('" +
        nome + "', '" + descricao + "', " + str(preco) + ")"
    )
    db.commit()
```

**Riscos:**
- `GET /produtos/1 OR 1=1` retorna todos os produtos
- `POST /produtos` com nome `', NULL, NULL); DELETE FROM produtos; --` deleta tudo

### Exemplo Depois

**Opção A: Prepared Statements (SQLite)**

```python
def get_produto_por_id(id):
    # Usar ? para placeholder
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    return cursor.fetchone()

def criar_produto(nome, descricao, preco):
    # Parâmetros separados da query
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco) VALUES (?, ?, ?)",
        (nome, descricao, preco)
    )
    db.commit()
```

**Opção B: ORM (SQLAlchemy) - Recomendado**

```python
from models.produto import Produto
from database import db

def get_produto_por_id(id):
    return Produto.query.get(id)

def criar_produto(nome, descricao, preco):
    produto = Produto(nome=nome, descricao=descricao, preco=preco)
    db.session.add(produto)
    db.session.commit()
    return produto
```

### Checklist de Validação
- [ ] Remover todas concatenações de strings em queries SQL
- [ ] Usar ? ou :param_name para placeholders
- [ ] Testar com valores maliciosos: `' OR 1=1`, `"; DROP TABLE`, etc
- [ ] Preferir ORM ao SQL raw quando possível
- [ ] Code review: verificar todas queries SQL

### Ferramentas
- Python: SQLAlchemy ORM, psycopg2 (prepared statements)
- Node: Sequelize ORM, parameterized queries

---

## Playbook #2: Securizar Credenciais

### Problema
Senhas, API keys, credenciais de banco hardcoded no código-fonte.

### Impacto
- 🔴 CRÍTICO: Acesso a produção comprometido

### Exemplo Antes

**File:** `utils.py` / `config.js`

```python
# ❌ Python
config = {
    'dbPass': 'admin_pass_123',
    'paymentKey': 'pk_live_xxxxx',
    'smtpPassword': 'gmail_password'
}

app.config['SECRET_KEY'] = 'super-secret-123'
```

```javascript
// ❌ Node.js
const config = {
    dbPassword: 'senha123',
    apiKey: 'sk_test_1234567890'
};
```

### Exemplo Depois

**Step 1: Criar arquivo .env**

```bash
# .env (NUNCA commitar!)
FLASK_ENV=development
DATABASE_URL=sqlite:///tasks.db
SECRET_KEY=xyz789-randomly-generated-secret-key-min-32-chars
PAYMENT_GATEWAY_KEY=pk_live_xxxxx
SMTP_PASSWORD=gmail_password
SMTP_USER=noreply@company.com
```

**Step 2: Adicionar .env ao .gitignore**

```bash
# .gitignore
.env
.env.local
.env.*.local
__pycache__/
*.pyc
node_modules/
```

**Step 3: Carregar variáveis no código**

**Python com python-dotenv:**

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    PAYMENT_GATEWAY_KEY = os.getenv('PAYMENT_GATEWAY_KEY')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_USER = os.getenv('SMTP_USER')
    DEBUG = os.getenv('FLASK_ENV') == 'development'

# app.py
from config import Config
app.config.from_object(Config)
```

**Node.js com dotenv:**

```javascript
// config.js
require('dotenv').config();

module.exports = {
    databaseUrl: process.env.DATABASE_URL,
    secretKey: process.env.SECRET_KEY,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpPassword: process.env.SMTP_PASSWORD
};
```

**Step 4: Em produção, usar Secret Manager**

```python
# Para AWS
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

SECRET_KEY = get_secret('prod/app/secret-key')
```

### Checklist
- [ ] Criar .env com todas as credenciais
- [ ] Adicionar .env ao .gitignore
- [ ] Remover hardcoded values do código
- [ ] Instalar python-dotenv ou dotenv
- [ ] Testar que variáveis são carregadas
- [ ] Em produção, usar Secret Manager (AWS, Azure, etc)
- [ ] Rotar credenciais regularmente
- [ ] Usar chaves fortes (mínimo 32 caracteres)

---

## Playbook #3: Implementar Autenticação JWT

### Problema
Endpoints publicamente acessíveis sem verificação de identidade.

### Impacto
- 🔴 CRÍTICO: Qualquer pessoa acessa dados de qualquer usuário

### Exemplo Antes

```python
# ❌ routes/task_routes.py - SEM AUTENTICAÇÃO
@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    return jsonify(task.to_dict())  # Qualquer pessoa consegue ver!

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    task.title = request.json['title']
    db.session.commit()
    return jsonify(task.to_dict())  # Qualquer pessoa consegue modificar!
```

### Exemplo Depois

**Step 1: Instalar dependências**

```bash
# Python
pip install flask-jwt-extended

# Node.js
npm install jsonwebtoken
```

**Step 2: Setup de autenticação**

```python
# config.py
class Config:
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hora
    JWT_ALGORITHM = 'HS256'

# app.py
from flask_jwt_extended import JWTManager

jwt = JWTManager()
jwt.init_app(app)
```

**Step 3: Criar endpoint de login**

```python
# routes/auth_routes.py
from flask_jwt_extended import create_access_token
from flask import Blueprint, request, jsonify
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Verificar credenciais
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Gerar JWT
    access_token = create_access_token(
        identity=user.id,
        additional_claims={'role': user.role}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200
```

**Step 4: Proteger rotas com @jwt_required**

```python
# routes/task_routes.py
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

def login_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        return f(current_user_id, *args, **kwargs)
    return decorated_function

@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(current_user_id, task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    
    return jsonify(task.to_dict()), 200

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(current_user_id, task_id):
    task = Task.query.get(task_id)
    
    # Verificar autorização (owner ou admin)
    if task.user_id != current_user_id and not is_admin(current_user_id):
        return jsonify({'error': 'Sem permissão'}), 403
    
    data = request.get_json()
    task.title = data.get('title', task.title)
    db.session.commit()
    
    return jsonify(task.to_dict()), 200
```

**Step 5: Autorização (Role-based)**

```python
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(current_user_id, *args, **kwargs):
        user = User.query.get(current_user_id)
        if user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        return f(current_user_id, *args, **kwargs)
    return decorated_function

@task_bp.route('/tasks/admin/report', methods=['GET'])
@admin_required
def admin_report(current_user_id):
    # Apenas admin consegue ver
    report = generate_report()
    return jsonify(report), 200
```

### Checklist
- [ ] Instalar flask-jwt-extended (ou equivalente)
- [ ] Configurar JWT_SECRET_KEY em .env
- [ ] Criar rota /login que gera token
- [ ] Adicionar @login_required a rotas protegidas
- [ ] Testar sem token (deve retornar 401)
- [ ] Testar com token inválido (deve retornar 401)
- [ ] Testar com token válido (deve funcionar)
- [ ] Implementar refresh tokens (opcional, mas recomendado)
- [ ] Usar HTTPS em produção

### Exemplo de uso (Cliente)

```bash
# Login para obter token
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "password123"}'

# Response:
# {"access_token": "eyJ0eXAiOiJKV1QiLC...", "user": {...}}

# Usar token para acessar rotas protegidas
curl -X GET http://localhost:5000/tasks \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLC..."
```

---

## Playbook #4: Hash de Senhas com Bcrypt

### Problema
Senhas armazenadas com MD5, SHA256, ou base64 (não criptografia).

### Impacto
- 🔴 CRÍTICO: Rainbow tables conseguem quebrar senhas em minutos

### Exemplo Antes

```python
# ❌ models/user.py
import hashlib

class User(db.Model):
    password = db.Column(db.String(255))
    
    def set_password(self, pwd):
        # ❌ MD5 é reversível com rainbow tables
        self.password = hashlib.md5(pwd.encode()).hexdigest()
    
    def check_password(self, pwd):
        return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### Exemplo Depois

**Python:**

```python
# requirements.txt
bcrypt==4.0.1

# models/user.py
import bcrypt

class User(db.Model):
    password = db.Column(db.String(255), nullable=False)
    
    def set_password(self, pwd):
        # ✅ Bcrypt com 12 rounds (padrão)
        salt = bcrypt.gensalt(rounds=12)
        self.password = bcrypt.hashpw(pwd.encode(), salt).decode()
    
    def check_password(self, pwd):
        # ✅ Verifica contra hash
        return bcrypt.checkpw(pwd.encode(), self.password.encode())
```

**Node.js:**

```javascript
// package.json
"bcrypt": "^5.1.0"

// models/user.js
const bcrypt = require('bcrypt');

class User {
    async setPassword(pwd) {
        // ✅ Bcrypt com 10 rounds
        const salt = await bcrypt.genSalt(10);
        this.password = await bcrypt.hash(pwd, salt);
    }
    
    async checkPassword(pwd) {
        return bcrypt.compare(pwd, this.password);
    }
}
```

### Checklist
- [ ] Instalar bcrypt
- [ ] Refatorar set_password() para usar bcrypt
- [ ] Refatorar check_password() para usar bcrypt.checkpw()
- [ ] NÃO retornar password em APIs (remover de to_dict())
- [ ] Testar password com valores válidos e inválidos
- [ ] Testar que senhas antigas ainda funcionam (se aplicável)
- [ ] Nunca armazenar senhas em texto plano
- [ ] Usar mínimo 12 rounds em produção (mais seguro, mais lento)

---

## Playbook #5: Otimizar N+1 Queries

### Problema
Loop que faz query adicional por iteração (1 + N queries).

### Impacto
- 🟠 HIGH: API lenta (100ms → 5s para 100 registros)

### Exemplo Antes

```python
# ❌ routes/task_routes.py
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()  # 1 query
    result = []
    
    for t in tasks:
        user = User.query.get(t.user_id)  # +1 query por task
        category = Category.query.get(t.category_id)  # +1 query por task
        
        result.append({
            'id': t.id,
            'title': t.title,
            'user_name': user.name if user else None,
            'category_name': category.name if category else None
        })
    
    # Total: 1 + (N*2) queries
    return jsonify(result), 200
```

### Exemplo Depois

**Opção A: Eager Loading com joinedload**

```python
# ✅ routes/task_routes.py
from sqlalchemy.orm import joinedload

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    # Eager load user e category (JOINs na mesma query)
    tasks = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category)
    ).all()  # 1 query com JOINs
    
    result = []
    for t in tasks:
        result.append({
            'id': t.id,
            'title': t.title,
            # Dados já carregados, sem queries adicionais!
            'user_name': t.user.name if t.user else None,
            'category_name': t.category.name if t.category else None
        })
    
    return jsonify(result), 200
```

**Opção B: Usar Repository com eager loading**

```python
# ✅ repositories/task_repository.py
from sqlalchemy.orm import joinedload

class TaskRepository:
    def find_all_with_relations(self):
        return Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category)
        ).all()

# ✅ routes/task_routes.py
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = TaskRepository().find_all_with_relations()
    result = [t.to_dict_with_relations() for t in tasks]
    return jsonify(result), 200
```

**Opção C: Query com JOIN explícito**

```python
# ✅ Query com JOINs
from sqlalchemy import join

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = db.session.query(Task, User, Category).outerjoin(
        User, Task.user_id == User.id
    ).outerjoin(
        Category, Task.category_id == Category.id
    ).all()
    
    result = []
    for task, user, category in tasks:
        result.append({
            'id': task.id,
            'title': task.title,
            'user_name': user.name if user else None,
            'category_name': category.name if category else None
        })
    
    return jsonify(result), 200
```

### Checklist
- [ ] Identificar loops com queries inside (grep pattern)
- [ ] Substituir por eager loading (joinedload/selectinload)
- [ ] Usar query profiling (print SQL antes/depois)
- [ ] Testar com 100+ registros
- [ ] Medir tempo de resposta antes/depois
- [ ] Verificar se há paginação para listas muito grandes
- [ ] Adicionar índices em foreign keys (banco já faz, mas verificar)

---

## Playbook #6: Converter Callbacks para Async/Await

### Problema
Múltiplos níveis de callbacks aninhados (Callback Hell).

### Impacto
- 🟠 HIGH: Código ilegível, race conditions, bugs difíceis de debugar

### Exemplo Antes (Node.js)

```javascript
// ❌ Callback Hell
app.get('/api/report', (req, res) => {
    db.all("SELECT * FROM courses", [], (err, courses) => {  // Nível 1
        let pending = courses.length;
        let report = [];
        
        courses.forEach(course => {
            db.all("SELECT * FROM enrollments WHERE course_id = ?", [course.id], (err, enrollments) => {  // Nível 2
                let enrollPending = enrollments.length;
                let courseData = { course: course.title };
                
                enrollments.forEach(enr => {
                    db.get("SELECT amount FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {  // Nível 3
                        courseData.revenue = payment.amount;
                        enrollPending--;
                        
                        if (enrollPending === 0) {
                            report.push(courseData);
                            pending--;
                            if (pending === 0) res.json(report);  // Finalmente retorna!
                        }
                    });
                });
            });
        });
    });
});
```

### Exemplo Depois

**Step 1: Promisify database functions**

```javascript
// ✅ utils/db-promise.js
const { promisify } = require('util');

const dbAll = promisify(db.all.bind(db));
const dbGet = promisify(db.get.bind(db));

module.exports = { dbAll, dbGet };
```

**Step 2: Usar async/await**

```javascript
// ✅ routes/report_routes.js
const { dbAll, dbGet } = require('../utils/db-promise');

app.get('/api/report', async (req, res) => {
    try {
        // Muito mais legível!
        const courses = await dbAll("SELECT * FROM courses");
        
        const report = await Promise.all(
            courses.map(async (course) => {
                const enrollments = await dbAll(
                    "SELECT * FROM enrollments WHERE course_id = ?",
                    [course.id]
                );
                
                let revenue = 0;
                for (const enr of enrollments) {
                    const payment = await dbGet(
                        "SELECT amount FROM payments WHERE enrollment_id = ?",
                        [enr.id]
                    );
                    if (payment) {
                        revenue += payment.amount;
                    }
                }
                
                return {
                    course: course.title,
                    revenue: revenue
                };
            })
        );
        
        res.json(report);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});
```

### Checklist
- [ ] Instalar promisify ou usar lib como util.promisify
- [ ] Converter callbacks para promises/async-await
- [ ] Usar try/catch para tratamento de erro
- [ ] Remover contadores manuais (callbacks)
- [ ] Usar Promise.all() para paralelizar
- [ ] Testar que erros são capturados corretamente
- [ ] Verificar que resposta é retornada apenas uma vez

---

## Playbook #7: Eliminar Código Duplicado

### Problema
Mesma lógica implementada em múltiplos lugares.

### Impacto
- 🟡 MEDIUM: Manutenção difícil, inconsistência entre versões

### Exemplo Antes

```python
# ❌ Lógica "is_overdue" duplicada 5 vezes

# task_routes.py - linhas 30-39
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False

# task_routes.py - linhas 71-80 (IDÊNTICA)
# user_routes.py - linhas 171-180 (IDÊNTICA)
# report_routes.py - linhas 34-43 (IDÊNTICA)
# report_routes.py - linhas 132-135 (IDÊNTICA)
```

### Exemplo Depois

**Step 1: Centralizar em modelo**

```python
# ✅ models/task.py
class Task(db.Model):
    # ... fields ...
    
    def is_overdue(self):
        """Verifica se task está atrasada e não foi concluída"""
        if not self.due_date:
            return False
        
        if self.due_date >= datetime.utcnow():
            return False
        
        return self.status not in ['done', 'cancelled']
```

**Step 2: Usar método em todas rotas**

```python
# ✅ task_routes.py
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    
    for t in tasks:
        task_data = t.to_dict()
        task_data['overdue'] = t.is_overdue()  # Simples!
        result.append(task_data)
    
    return jsonify(result), 200

# ✅ user_routes.py
@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    
    for t in tasks:
        task_data = t.to_dict()
        task_data['overdue'] = t.is_overdue()  # Mesma chamada
        result.append(task_data)
    
    return jsonify(result), 200

# ✅ report_routes.py
@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    tasks = Task.query.all()
    overdue_count = 0
    
    for t in tasks:
        if t.is_overdue():  # Reutilizar
            overdue_count += 1
    
    return jsonify({
        'overdue': overdue_count
    }), 200
```

### Checklist
- [ ] Identificar código duplicado (buscar por patterns)
- [ ] Criar método/função reutilizável
- [ ] Remover duplicatas e usar função centralizada
- [ ] Testar que comportamento é idêntico
- [ ] Code review: confirmar que não há outras duplicatas

---

## Playbook #8: Remover Global Variables

### Problema
Variáveis globais mutáveis causam race conditions e vazamento de dados.

### Impacto
- 🟡 MEDIUM: Race conditions, estado inconsistente, vazamento de dados

### Exemplo Antes

```python
# ❌ utils.py - Estado global
globalCache = {}
totalRevenue = 0

def logAndCache(key, data):
    globalCache[key] = data  # Compartilhado entre requisições!
```

```javascript
// ❌ AppManager.js - Conexão global
let db_connection = null;

function getDb() {
    if (db_connection === null) {
        db_connection = sqlite3.connect(':memory:');
        // Sem sincronização, múltiplas threads acessam simultaneamente
    }
    return db_connection;
}
```

### Exemplo Depois

**Opção A: Request-scoped (Flask)**

```python
# ✅ app.py - Usar g para escopo de requisição
from flask import g

@app.before_request
def before_request():
    # Criar espaço isolado por requisição
    g.cache = {}

# ✅ services/cache_service.py
from flask import g

class CacheService:
    @staticmethod
    def set(key, value):
        g.cache[key] = value
    
    @staticmethod
    def get(key):
        return g.cache.get(key)
```

**Opção B: Redis (distribuído, produção)**

```python
# ✅ config.py
import redis

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# ✅ services/cache_service.py
from config import redis_client
import json

class CacheService:
    @staticmethod
    def set(key, value, expire=3600):
        redis_client.setex(f"cache:{key}", expire, json.dumps(value))
    
    @staticmethod
    def get(key):
        value = redis_client.get(f"cache:{key}")
        return json.loads(value) if value else None
```

**Opção C: Connection pooling (Node.js)**

```javascript
// ✅ database.js - Pool de conexões
const sqlite3 = require('sqlite3').verbose();

class DatabasePool {
    constructor(size = 10) {
        this.pool = [];
        for (let i = 0; i < size; i++) {
            this.pool.push(new sqlite3.Database(':memory:'));
        }
    }
    
    getConnection() {
        if (this.pool.length === 0) {
            return new sqlite3.Database(':memory:');
        }
        return this.pool.pop();
    }
    
    releaseConnection(conn) {
        if (this.pool.length < 10) {
            this.pool.push(conn);
        }
    }
}

module.exports = new DatabasePool();
```

### Checklist
- [ ] Identificar variáveis globais mutáveis
- [ ] Usar request-scoped (g) para caso simples
- [ ] Usar Redis para distribuído/produção
- [ ] Remover referências globais
- [ ] Testar com múltiplas requisições simultâneas
- [ ] Verificar que não há vazamento de dados entre usuários

---

## Playbook #9: Exception Handling Robusto

### Problema
Capturar `Exception` genérica esconde bugs reais.

### Impacto
- 🟡 MEDIUM: Debugging impossível, mensagens inúteis

### Exemplo Antes

```python
# ❌ Captura genérica
@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        user = User()
        user.name = data['name']
        user.email = data['email']
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
    except:  # Captura TUDO!
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar usuário'}), 500
```

### Exemplo Depois

```python
# ✅ Capturar exceções específicas
from sqlalchemy.exc import IntegrityError, OperationalError
import logging

logger = logging.getLogger(__name__)

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        user = User()
        user.name = data['name']
        user.email = data['email']
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
    
    except IntegrityError:
        db.session.rollback()
        # Email já cadastrado
        return jsonify({'error': 'Email já cadastrado'}), 409
    
    except OperationalError:
        db.session.rollback()
        # Erro de conexão com banco
        logger.error("Erro de conexão com banco")
        return jsonify({'error': 'Serviço indisponível'}), 503
    
    except ValueError as e:
        # Erro de validação
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        db.session.rollback()
        # Log do erro real (nunca retornar stack trace em produção)
        logger.exception(f"Erro inesperado ao criar usuário")
        return jsonify({'error': 'Erro interno'}), 500
```

### Checklist
- [ ] Remover `except Exception:` ou `except:` genéricos
- [ ] Capturar exceções específicas (IntegrityError, ValueError, etc)
- [ ] Usar logging para errors não-esperados
- [ ] Retornar status HTTP apropriado (409, 503, 400, 500)
- [ ] Nunca retornar stack trace em produção
- [ ] Testar que cada exceção é tratada corretamente

---

## Playbook #10: Validação Centralizada

### Problema
Validação espalhada ou ausente em múltiplas rotas.

### Impacto
- 🟡 MEDIUM: Dados inválidos no banco, inconsistência

### Exemplo Antes

```python
# ❌ Validação espalhada
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    
    if len(title) < 3:  # Validação aqui
        return jsonify({'error': 'Título muito curto'}), 400
    
    # Mas em outro endpoint...
    @user_bp.route('/users', methods=['POST'])
    def create_user():
        name = data.get('name')
        # Sem validação de comprimento!
        # Permite "<script>xss</script>"
```

### Exemplo Depois

**Step 1: Usar Marshmallow para schemas**

```python
# ✅ validators/task_validator.py
from marshmallow import Schema, fields, validate, ValidationError

class TaskCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=3, max=200),
        error_messages={'required': 'Título é obrigatório'}
    )
    description = fields.String(allow_none=True)
    status = fields.String(
        validate=validate.OneOf(['pending', 'in_progress', 'done', 'cancelled']),
        missing='pending'
    )
    priority = fields.Integer(
        validate=validate.Range(min=1, max=5),
        missing=3
    )
    due_date = fields.DateTime(format='%Y-%m-%d', allow_none=True)

class TaskUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String()
    status = fields.String(validate=validate.OneOf(['pending', 'in_progress', 'done', 'cancelled']))
    priority = fields.Integer(validate=validate.Range(min=1, max=5))
    due_date = fields.DateTime(format='%Y-%m-%d', allow_none=True)

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
```

**Step 2: Usar schemas nas rotas**

```python
# ✅ routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task(current_user_id):
    try:
        # Validação e deserialização automática
        data = task_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # Dados garantidamente válidos
    task = TaskService.create(data, current_user_id)
    return jsonify(task.to_dict()), 201

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(current_user_id, task_id):
    try:
        data = task_update_schema.load(request.get_json(), partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    task = TaskService.update(task_id, data, current_user_id)
    return jsonify(task.to_dict()), 200
```

### Checklist
- [ ] Instalar Marshmallow (ou Joi para Node.js)
- [ ] Criar schemas para cada operação (create, update, etc)
- [ ] Usar schema.load() para validar entrada
- [ ] Remover validações manuais das rotas
- [ ] Testar com dados inválidos
- [ ] Testar com dados válidos
- [ ] Retornar mensagens de validação claras

---

## Playbook #11: Substituir APIs Deprecated

### Problema
Código chama funções/métodos que a linguagem, framework ou biblioteca já marcaram como deprecated — funciona hoje, mas gera warnings e quebra em upgrades futuros.

### Impacto
- 🟡 MEDIUM: dívida técnica silenciosa; upgrade de dependência pode quebrar produção sem aviso

### Exemplo Antes

```python
# ❌ Python — deprecated desde 3.12
from datetime import datetime

class Task(db.Model):
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_overdue(self):
        return self.due_date < datetime.utcnow()
```

```javascript
// ❌ Node.js — Buffer() deprecated desde Node 6
function encode(payload) {
    return new Buffer(payload).toString('base64');
}
```

### Exemplo Depois

**Step 1: Buscar todas as ocorrências**

```bash
grep -rn "datetime.utcnow\|new Buffer(" --include="*.py" --include="*.js"
```

**Step 2: Substituir pela API atual, mantendo o comportamento**

```python
# ✅ Python — timezone-aware, API atual
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc)

class Task(db.Model):
    created_at = db.Column(db.DateTime, default=_now)

    def is_overdue(self):
        return self.due_date < _now()
```

```javascript
// ✅ Node.js — API atual
function encode(payload) {
    return Buffer.from(payload).toString('base64');
}
```

**Step 3: Validar**

```bash
# Rodar a app/testes e confirmar que não há mais DeprecationWarning no output
pytest -q  # ou: npm test
```

### Checklist
- [ ] Grep pelas APIs deprecated conhecidas da stack detectada na Fase 1
- [ ] Substituir cada ocorrência pela API atual equivalente (mesmo comportamento observável)
- [ ] Rodar a aplicação e a suíte de testes e confirmar ausência de `DeprecationWarning`/`FutureWarning`
- [ ] Conferir o changelog da versão instalada de cada dependência principal

---

## Playbook #12: Eliminar Magic Numbers e Renomear Variáveis

### Problema
Valores soltos sem nome (`0.85`, `16`, `3600000`) e variáveis abreviadas (`u`, `t`, `cc`) tornam o código difícil de ler e de alterar com segurança.

### Impacto
- 🔵 LOW: legibilidade e velocidade de manutenção, sem risco funcional imediato

### Exemplo Antes

```python
# ❌ Magic numbers e nomes abreviados
def calcular_desconto(p, qtd):
    if qtd > 10:
        return p * 0.85
    return p
```

```javascript
// ❌ Magic numbers e nomes abreviados
function processarPagamento(cc, e, u) {
    if (cc.length !== 16) { throw new Error('Cartão inválido'); }
}
```

### Exemplo Depois

**Step 1: Extrair constantes nomeadas**

```python
# ✅ Python
DESCONTO_ATACADO = 0.85
QUANTIDADE_MINIMA_ATACADO = 10

def calcular_desconto(preco, quantidade):
    if quantidade > QUANTIDADE_MINIMA_ATACADO:
        return preco * DESCONTO_ATACADO
    return preco
```

```javascript
// ✅ Node.js
const CREDIT_CARD_LENGTH = 16;

function processarPagamento(creditCard, email, user) {
    if (creditCard.length !== CREDIT_CARD_LENGTH) {
        throw new Error('Cartão inválido');
    }
}
```

**Step 2: Renomear parâmetros/variáveis abreviados em todo o arquivo** (buscar por variáveis de 1-2 letras fora de laços curtos e renomear para o nome completo do domínio).

### Checklist
- [ ] Grep por literais numéricos repetidos ou não-óbvios fora de testes
- [ ] Extrair para constantes com nome que explique o "porquê"
- [ ] Renomear variáveis/parâmetros de 1-2 letras (exceto índices de loop locais)
- [ ] Rodar a suíte de testes para garantir que o comportamento não mudou

---

## Resumo de Playbooks

| Playbook | Severidade | Tempo Estimado |
|----------|-----------|----------------|
| #1 SQL Injection | CRITICAL | 2-4 horas |
| #2 Credenciais | CRITICAL | 1-2 horas |
| #3 Autenticação JWT | CRITICAL | 4-6 horas |
| #4 Bcrypt Passwords | CRITICAL | 1-2 horas |
| #5 N+1 Queries | HIGH | 2-3 horas |
| #6 Async/Await | HIGH | 3-4 horas |
| #7 Duplicação | MEDIUM | 2-3 horas |
| #8 Global Variables | MEDIUM | 1-2 horas |
| #9 Exception Handling | MEDIUM | 2-3 horas |
| #10 Validação | MEDIUM | 2-3 horas |
| #11 APIs Deprecated | MEDIUM | 1-2 horas |
| #12 Magic Numbers / Nomenclatura | LOW | 1-2 horas |

**Total:** ~27-39 horas de refatoração (depende do projeto)

---

## Próximos Passos

1. Leia `heuristics.md` para validar refatoração
2. Use `report-template.md` para documentar progresso
3. Execute testes após cada playbook
