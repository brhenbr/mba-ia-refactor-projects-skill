# Anti-Patterns & Code Smells

Catálogo de 12+ anti-patterns identificados em projetos legados, com severidade, impacto, exemplos e estratégias de correção. Cobre as quatro severidades (CRITICAL, HIGH, MEDIUM, LOW) e inclui detecção de APIs/métodos deprecated.

---

## 1. SQL Injection via String Concatenation

**Severidade:** 🔴 CRITICAL  
**Categoria:** Segurança  
**Frequência:** Muito Alto em código legado

### Descrição
Construir queries SQL por concatenação de strings em vez de prepared statements permite que atacantes injetem código SQL malicioso através de parâmetros de entrada.

### Impacto
- **Segurança:** Acesso não autorizado a dados, roubo de informações, exclusão/modificação de dados
- **Conformidade:** OWASP Top 10 #1 (Injection), CVSS crítico
- **Negócio:** Vazamento de dados, perda de confiança do cliente, multas regulatórias

### Exemplo Problemático

```python
# ❌ Python/SQLite - VULNERÁVEL
def get_produto_por_id(id):
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    return cursor.fetchone()

# Ataque: GET /produtos/1 OR 1=1
# Query executada: SELECT * FROM produtos WHERE id = 1 OR 1=1
# Resultado: Retorna todos os produtos
```

```javascript
// ❌ Node.js/SQLite - VULNERÁVEL
app.get('/users/:id', (req, res) => {
    let id = req.params.id;
    db.all("SELECT * FROM users WHERE id = " + id, (err, rows) => {
        res.json(rows);
    });
});

// Ataque: GET /users/1; DROP TABLE users; --
// Query executada: SELECT * FROM users WHERE id = 1; DROP TABLE users; --
// Resultado: Tabela users é deletada
```

### Solução ✅

```python
# ✅ Python/SQLAlchemy (ORM)
def get_produto_por_id(id):
    product = Product.query.get(id)
    return product.to_dict() if product else None

# ✅ Python/SQLite (Prepared Statements)
def get_produto_por_id(id):
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    return cursor.fetchone()
```

```javascript
// ✅ Node.js/SQLite (Prepared Statements)
app.get('/users/:id', (req, res) => {
    let id = req.params.id;
    db.get("SELECT * FROM users WHERE id = ?", [id], (err, row) => {
        res.json(row);
    });
});

// ✅ Node.js/Sequelize (ORM)
app.get('/users/:id', async (req, res) => {
    const user = await User.findByPk(req.params.id);
    res.json(user);
});
```

### Regras
- ✅ **SEMPRE** use prepared statements com placeholders (?, $1, :param)
- ✅ Use ORM (SQLAlchemy, Sequelize, TypeORM) quando possível
- ✅ NUNCA concatene user input em queries
- ✅ Valide e sanitize entrada mesmo com prepared statements (defesa em profundidade)

### Playbook
Veja `refactoring-playbook.md` → **Playbook #1: Eliminar SQL Injection**

---

## 2. Credenciais Hardcoded no Código-Fonte

**Severidade:** 🔴 CRITICAL  
**Categoria:** Segurança  
**Frequência:** Muito Alto

### Descrição
Armazenar senhas, API keys, tokens e credenciais de banco diretamente no código permite acesso não autorizado a sistemas externos e produção.

### Impacto
- **Segurança:** Comprometimento de produção, acesso a sistemas terceiros
- **Conformidade:** PCI-DSS, GDPR, SOC 2 falham
- **Negócio:** Vazamento de dados massivo, serviços externos comprometidos

### Exemplo Problemático

```python
# ❌ utils.py
config = {
    'dbPass': 'senha_super_secreta_prod_123',
    'paymentGatewayKey': 'pk_live_1234567890abcdef',
    'smtpPassword': 'gmail_password_123'
}

app.config['SECRET_KEY'] = 'super-secret-key-123'
```

```javascript
// ❌ database.js
const config = {
    dbUser: 'admin_master',
    dbPass: 'senha123',
    apiKey: 'sk_test_1234567890'
};
```

### Solução ✅

```python
# ✅ app.py com python-dotenv
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
```

```bash
# ✅ .env (NUNCA commitar este arquivo)
SECRET_KEY=xyz789-randomly-generated-secret-key
DATABASE_URL=postgresql://user:password@host/db
PAYMENT_GATEWAY_KEY=pk_live_xxxxx
SMTP_PASSWORD=senha_super_segura
```

```javascript
// ✅ config.js com dotenv
require('dotenv').config();

module.exports = {
    dbPass: process.env.DB_PASSWORD,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    secretKey: process.env.SECRET_KEY
};
```

### Regras
- ✅ Use variáveis de ambiente (dotenv, env files, secrets managers)
- ✅ Adicione `.env` ao `.gitignore`
- ✅ Em produção, use secret managers (AWS Secrets Manager, Vault, etc)
- ✅ Rotate credenciais regularmente
- ✅ Use chaves fortes e aleatórias (mínimo 32 caracteres)
- ✅ Nunca commite `.env` ou arquivos com credenciais

### Playbook
Veja `refactoring-playbook.md` → **Playbook #2: Securizar Credenciais**

---

## 3. Autenticação e Autorização Ausentes

**Severidade:** 🔴 CRITICAL  
**Categoria:** Segurança  
**Frequência:** Alto

### Descrição
Endpoints publicamente acessíveis sem validação de identidade (autenticação) e permissões (autorização) permitem que qualquer usuário acesse/modifique dados de outros.

### Impacto
- **Segurança:** Acesso não autorizado, modificação de dados alheios, privilégios elevados
- **Conformidade:** OWASP Top 10 #2 (Broken Authentication), #1 (Access Control)
- **Negócio:** Vazamento de dados pessoais, responsabilidade civil

### Exemplo Problemático

```python
# ❌ routes/task_routes.py - SEM AUTENTICAÇÃO
@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    # Qualquer pessoa consegue modificar qualquer task
    task = Task.query.get(task_id)
    task.title = request.json['title']
    db.session.commit()
    return jsonify(task.to_dict())

# ❌ routes/user_routes.py - SEM AUTORIZAÇÃO
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Qualquer pessoa consegue deletar qualquer usuário
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuário deletado'})
```

```javascript
// ❌ routes/admin.js - SEM AUTENTICAÇÃO
app.get('/api/admin/financial-report', (req, res) => {
    // Qualquer pessoa consegue ver dados financeiros sensíveis
    const report = db.all("SELECT * FROM payments");
    res.json(report);
});
```

### Solução ✅

```python
# ✅ Middleware de autenticação JWT
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

def login_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        return f(current_user_id, *args, **kwargs)
    return decorated_function

# ✅ Decorator de autorização
def owner_or_admin_required(f):
    @wraps(f)
    def decorated_function(current_user_id, *args, **kwargs):
        resource_id = kwargs.get('user_id')
        user = User.query.get(current_user_id)
        
        if user.role != 'admin' and current_user_id != resource_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        return f(current_user_id, *args, **kwargs)
    return decorated_function

# ✅ Aplicando autenticação e autorização
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@owner_or_admin_required
def delete_user(current_user_id, user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuário deletado'}), 200
```

```javascript
// ✅ Middleware JWT Express
const express = require('express');
const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'Sem token' });
    }
    
    try {
        const decoded = jwt.verify(token, process.env.SECRET_KEY);
        req.user = decoded;
        next();
    } catch (err) {
        res.status(403).json({ error: 'Token inválido' });
    }
};

const adminOnly = (req, res, next) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Acesso negado' });
    }
    next();
};

// ✅ Aplicando middleware
app.delete('/api/users/:id', authMiddleware, adminOnly, (req, res) => {
    // Apenas admin autenticado consegue deletar
    db.run("DELETE FROM users WHERE id = ?", [req.params.id], (err) => {
        res.json({ message: 'Usuário deletado' });
    });
});
```

### Regras
- ✅ **TODAS** as rotas precisam de autenticação (exceto /login, /register, /health)
- ✅ Use JWT (JSON Web Tokens) ou sessions seguras
- ✅ Implemente autorização baseada em roles/permissões (RBAC)
- ✅ Validar identidade do usuário antes de retornar dados pessoais
- ✅ Checar propriedade (um usuário só modifica dados próprios, não de outros)
- ✅ Endpoints admin exigem role='admin'

### Playbook
Veja `refactoring-playbook.md` → **Playbook #3: Implementar Autenticação JWT**

---

## 4. Criptografia Fraca ou Inadequada de Senhas

**Severidade:** 🔴 CRITICAL  
**Categoria:** Segurança  
**Frequência:** Muito Alto

### Descrição
Usar MD5, SHA1, base64 ou sem salt para armazenar senhas compromete a segurança mesmo que o banco seja roubado. Atacantes conseguem fazer brute force/rainbow tables rapidamente.

### Impacto
- **Segurança:** Senhas reversíveis com rainbow tables, brute force rápido
- **Conformidade:** OWASP, NIST, PCI-DSS exigem bcrypt/argon2
- **Negócio:** Comprometimento de contas de usuários, identidade roubada

### Exemplo Problemático

```python
# ❌ Python com MD5 (CRIPTOGRAFICAMENTE QUEBRADO)
import hashlib

def set_password(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()

# ❌ Base64 (NÃO É CRIPTOGRAFIA, É ENCODING)
import base64

def set_password(pwd):
    return base64.b64encode(pwd.encode()).decode()

# ❌ Sem salt
def set_password(pwd):
    return hashlib.sha256(pwd).hexdigest()
```

```javascript
// ❌ Node.js com MD5
const crypto = require('crypto');

function setPassword(pwd) {
    return crypto.createHash('md5').update(pwd).digest('hex');
}

// ❌ Sem salt e sem iterações
function setPassword(pwd) {
    return crypto.createHash('sha256').update(pwd).digest('hex');
}
```

### Solução ✅

```python
# ✅ Python com bcrypt
import bcrypt

def set_password(pwd):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd.encode(), salt).decode()

def check_password(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())

# ✅ Alternativa: Argon2
from argon2 import PasswordHasher

hasher = PasswordHasher()

def set_password(pwd):
    return hasher.hash(pwd)

def check_password(pwd, hashed):
    try:
        hasher.verify(hashed, pwd)
        return True
    except:
        return False
```

```javascript
// ✅ Node.js com bcrypt
const bcrypt = require('bcrypt');

async function setPassword(pwd) {
    const salt = await bcrypt.genSalt(10);
    return bcrypt.hash(pwd, salt);
}

async function checkPassword(pwd, hashed) {
    return bcrypt.compare(pwd, hashed);
}

// ✅ Alternativa: Argon2
const argon2 = require('argon2');

async function setPassword(pwd) {
    return argon2.hash(pwd);
}

async function checkPassword(pwd, hashed) {
    return argon2.verify(hashed, pwd);
}
```

### Regras
- ✅ **NUNCA** use MD5, SHA1, SHA256 direto (sem salt/iterações)
- ✅ **SEMPRE** use bcrypt (12+ rounds) ou Argon2
- ✅ Salt é gerado automaticamente por bcrypt/argon2
- ✅ **NUNCA** armazene passwords em texto plano
- ✅ **NUNCA** retorne hash em APIs (nem em to_dict())
- ✅ Senhas devem ter mínimo 8 caracteres (12+ recomendado)

### Playbook
Veja `refactoring-playbook.md` → **Playbook #4: Hash de Senhas com Bcrypt**

---

## 5. N+1 Query Problem (Ineficiência de Banco)

**Severidade:** 🟠 HIGH  
**Categoria:** Performance  
**Frequência:** Muito Alto

### Descrição
Fazer uma query inicial + N queries adicionais dentro de um loop resulta em centenas de queries desnecessárias, degradando performance exponencialmente.

### Impacto
- **Performance:** API lenta (100ms → 5s para retornar 100 registros)
- **Escalabilidade:** Não aguenta carga de produção
- **Custo:** Database sobrecarga, timeout de conexões

### Exemplo Problemático

```python
# ❌ Python/SQLAlchemy - N+1 QUERIES
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()  # 1 query
    result = []
    
    for t in tasks:  # Para cada task...
        user = User.query.get(t.user_id)  # +1 query
        category = Category.query.get(t.category_id)  # +1 query
        
        result.append({
            'id': t.id,
            'title': t.title,
            'user_name': user.name if user else None,
            'category_name': category.name if category else None
        })
    
    # Total: 1 + (N*2) queries
    # Se N=100 tasks → 201 queries! ❌
    return jsonify(result)
```

```javascript
// ❌ Node.js/SQLite - N+1 QUERIES
app.get('/api/courses/:id/students', (req, res) => {
    db.get("SELECT * FROM courses WHERE id = ?", [req.params.id], (err, course) => {
        // 1 query
        
        db.all("SELECT * FROM enrollments WHERE course_id = ?", [course.id], (err, enrollments) => {
            // 1 query
            
            let students = [];
            enrollments.forEach(enr => {
                db.get("SELECT * FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                    // +1 query por matrícula
                    students.push(user);
                });
            });
            
            res.json(students);
        });
    });
});
```

### Solução ✅

```python
# ✅ Python/SQLAlchemy - EAGER LOADING com joinedload
from sqlalchemy.orm import joinedload

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    # Eager load user e category em uma query com JOINs
    tasks = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category)
    ).all()  # 1 query + JOINs
    
    result = []
    for t in tasks:  # Sem queries adicionais!
        result.append({
            'id': t.id,
            'title': t.title,
            'user_name': t.user.name if t.user else None,
            'category_name': t.category.name if t.category else None
        })
    
    return jsonify(result)

# ✅ Alternativa com selectinload (melhor para relações many-to-many)
from sqlalchemy.orm import selectinload

tasks = Task.query.options(
    selectinload(Task.user),
    selectinload(Task.category)
).all()
```

```javascript
// ✅ Node.js - Query com JOIN (melhor)
app.get('/api/courses/:id/students', (req, res) => {
    const query = `
        SELECT u.*, e.enrollment_id
        FROM users u
        JOIN enrollments e ON u.id = e.user_id
        JOIN courses c ON c.id = e.course_id
        WHERE c.id = ?
    `;
    
    db.all(query, [req.params.id], (err, students) => {
        res.json(students);
    });
});

// ✅ Ou com ORM (Sequelize)
app.get('/api/courses/:id/students', async (req, res) => {
    const course = await Course.findByPk(req.params.id, {
        include: [{ association: 'enrollments', include: ['user'] }]
    });
    
    const students = course.enrollments.map(e => e.user);
    res.json(students);
});
```

### Regras
- ✅ Use `eager loading` (joinedload, selectinload, include)
- ✅ Prefira JOINs em queries em vez de loops
- ✅ Use ORM features para lazy/eager loading config
- ✅ Sempre profile com database logging ativo
- ✅ Para relações many-to-many, use selectinload não joinedload
- ✅ Considere paginação para listas grandes

### Playbook
Veja `refactoring-playbook.md` → **Playbook #5: Otimizar N+1 Queries**

---

## 6. Callback Hell / Inversion of Control

**Severidade:** 🟠 HIGH  
**Categoria:** Manutenibilidade  
**Frequência:** Muito Alto em Node.js legado

### Descrição
Múltiplos níveis de callbacks aninhados (3+ níveis) tornam o código ilegível, difícil de debugar e propenso a race conditions.

### Impacto
- **Manutenibilidade:** Código "Piramide da Perdição", difícil compreender fluxo
- **Bugs:** Race conditions, tratamento de erro ineficaz
- **Performance:** Callbacks assincronos podem executar fora de ordem

### Exemplo Problemático

```javascript
// ❌ Callback Hell (Node.js)
app.get('/api/admin/financial-report', (req, res) => {
    db.all("SELECT * FROM courses", [], (err, courses) => {  // Nível 1
        if (err) return res.status(500).send("Erro");
        
        let coursesPending = courses.length;
        let report = [];
        
        courses.forEach(c => {
            db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {  // Nível 2
                if (err) return res.status(500).send("Erro");
                
                let enrPending = enrollments.length;
                let courseData = { course: c.title, revenue: 0 };
                
                enrollments.forEach(enr => {
                    db.get("SELECT * FROM users WHERE id = ?", [enr.user_id], (err, user) => {  // Nível 3
                        if (err) return res.status(500).send("Erro");
                        
                        db.get("SELECT amount FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {  // Nível 4
                            if (err) return res.status(500).send("Erro");
                            
                            courseData.revenue += payment.amount;
                            enrPending--;
                            
                            if (enrPending === 0) {
                                report.push(courseData);
                                coursesPending--;
                                if (coursesPending === 0) {
                                    res.json(report);  // Finalmente retorna!
                                }
                            }
                        });
                    });
                });
            });
        });
    });
});
```

### Solução ✅

```javascript
// ✅ Promises com async/await (MUITO mais legível)
app.get('/api/admin/financial-report', async (req, res) => {
    try {
        const courses = await db.allAsync("SELECT * FROM courses");
        
        const report = await Promise.all(
            courses.map(async (course) => {
                const enrollments = await db.allAsync(
                    "SELECT * FROM enrollments WHERE course_id = ?",
                    [course.id]
                );
                
                let revenue = 0;
                for (const enr of enrollments) {
                    const payment = await db.getAsync(
                        "SELECT amount FROM payments WHERE enrollment_id = ?",
                        [enr.id]
                    );
                    revenue += payment?.amount || 0;
                }
                
                return {
                    course: course.title,
                    revenue: revenue
                };
            })
        );
        
        res.json(report);
    } catch (err) {
        res.status(500).json({ error: 'Erro interno' });
    }
});

// ✅ Promisified version com util.promisify
const { promisify } = require('util');

const dbAll = promisify(db.all.bind(db));
const dbGet = promisify(db.get.bind(db));

app.get('/api/admin/financial-report', async (req, res) => {
    try {
        const courses = await dbAll("SELECT * FROM courses");
        
        const report = await Promise.all(
            courses.map(async (c) => {
                const enrollments = await dbAll(
                    "SELECT * FROM enrollments WHERE course_id = ?",
                    [c.id]
                );
                
                let revenue = 0;
                for (const enr of enrollments) {
                    const payment = await dbGet(
                        "SELECT amount FROM payments WHERE enrollment_id = ?",
                        [enr.id]
                    );
                    if (payment) revenue += payment.amount;
                }
                
                return { course: c.title, revenue };
            })
        );
        
        res.json(report);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});
```

### Regras
- ✅ Máximo 2 níveis de callbacks (preferir 0-1)
- ✅ Use async/await em Node.js (ECMAScript 2017+)
- ✅ Use Promises para operações assincronizadas
- ✅ Sempre use try/catch com async/await
- ✅ Nunca ignore erros em callbacks
- ✅ Use Promise.all() para paralelizar operações independentes

### Playbook
Veja `refactoring-playbook.md` → **Playbook #6: Converter Callbacks para Async/Await**

---

## 7. Código Duplicado (DRY Violation)

**Severidade:** 🟡 MEDIUM  
**Categoria:** Manutenibilidade  
**Frequência:** Muito Alto

### Descrição
Mesma lógica implementada em múltiplos lugares dificulta manutenção, aumenta bugs quando uma cópia é atualizada mas as outras não.

### Impacto
- **Manutenibilidade:** Mudança simples requer atualizar múltiplos locais
- **Bugs:** Inconsistência entre implementações
- **Testabilidade:** Precisa testar lógica múltiplas vezes

### Exemplo Problemático

```python
# ❌ Lógica "is_overdue" duplicada 5 vezes em task_routes.py

# Ocorrência 1 (linhas 30-39)
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

# Ocorrência 2 (linhas 71-80) - IDÊNTICA
if task.due_date:
    if task.due_date < datetime.utcnow():
        if task.status != 'done' and task.status != 'cancelled':
            data['overdue'] = True
        else:
            data['overdue'] = False
    else:
        data['overdue'] = False
else:
    data['overdue'] = False

# Ocorrência 3 (user_routes.py 171-180) - IDÊNTICA
# Ocorrência 4 (report_routes.py 34-43) - IDÊNTICA
# Ocorrência 5 (report_routes.py 132-135) - IDÊNTICA
```

### Solução ✅

```python
# ✅ Refatorar para método reutilizável em models/task.py
class Task(db.Model):
    # ... fields ...
    
    def is_overdue(self):
        """Verifica se task está atrasada e não foi concluída"""
        if not self.due_date:
            return False
        
        if self.due_date >= datetime.utcnow():
            return False
        
        return self.status not in ['done', 'cancelled']

# ✅ Usar método em todas as rotas
@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        data = task.to_dict()
        data['overdue'] = task.is_overdue()  # Simples!
        return jsonify(data), 200
    return jsonify({'error': 'Task não encontrada'}), 404
```

### Regras
- ✅ DRY (Don't Repeat Yourself) - escrever código uma vez
- ✅ Lógica reutilizável vai em métodos/funções
- ✅ Usar helper functions em services
- ✅ Usar mixins/traits para comportamento comum
- ✅ Centralizar validações em um lugar

### Playbook
Veja `refactoring-playbook.md` → **Playbook #7: Eliminar Código Duplicado**

---

## 8. Variáveis Globais e Mutable State

**Severidade:** 🟡 MEDIUM  
**Categoria:** Manutenibilidade / Segurança  
**Frequência:** Alto

### Descrição
Usar variáveis globais mutáveis causa efeitos colaterais não previstos, race conditions em ambientes multi-threaded, e estado compartilhado invisível.

### Impacto
- **Bugs:** Race conditions, estado inconsistente entre requisições
- **Testabilidade:** Testes afetam uns aos outros por estado global
- **Segurança:** Cache global vaza dados entre usuários

### Exemplo Problemático

```python
# ❌ utils.py - Estado global mutável
globalCache = {}
totalRevenue = 0

def logAndCache(key, data):
    globalCache[key] = data  # Compartilhado entre requisições!

# ❌ Risco de vazamento de dados
# Requisição 1: logAndCache('last_checkout_user_1', 'Curso A')
# Requisição 2: Consegue acessar globalCache['last_checkout_user_1']
```

```javascript
// ❌ AppManager.js - Conexão global não thread-safe
let db_connection = null;

function getDb() {
    if (db_connection === null) {
        db_connection = sqlite3.connect(':memory:');
        // Sem check_same_thread, múltiplas threads acessam simultaneamente
    }
    return db_connection;
}
```

### Solução ✅

```python
# ✅ Redis para cache em produção, request-scoped em testes
from flask import g

@app.before_request
def before_request():
    # Escopo por requisição, não global
    g.cache = {}

def logAndCache(key, data):
    g.cache[key] = data  # Isolado por requisição

# ✅ Em produção com Redis
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

def logAndCache(key, data):
    redis_client.set(f"cache:{key}", json.dumps(data), ex=3600)
```

```javascript
// ✅ Connection pooling com thread-safety
const sqlite3 = require('sqlite3').verbose();

class DatabaseManager {
    constructor() {
        this.pool = [];
    }
    
    getConnection() {
        // Pool de conexões, não global única
        if (this.pool.length === 0) {
            return new sqlite3.Database(':memory:');
        }
        return this.pool.pop();
    }
    
    releaseConnection(conn) {
        this.pool.push(conn);
    }
}

const dbManager = new DatabaseManager();
```

### Regras
- ✅ Evite variáveis globais mutáveis
- ✅ Use contexto por requisição (g em Flask, res.locals em Express)
- ✅ Para cache distribuído, use Redis, Memcached, não memória
- ✅ Use Dependency Injection em vez de globals
- ✅ Connection pooling para banco de dados

### Playbook
Veja `refactoring-playbook.md` → **Playbook #8: Remover Global Variables**

---

## 9. Exception Handling Genérico Demais

**Severidade:** 🟡 MEDIUM  
**Categoria:** Qualidade de Código  
**Frequência:** Muito Alto

### Descrição
Capturar `Exception` genericamente (ou em JavaScript `catch` sem discriminação) esconde bugs reais e torna debugging impossível.

### Impacto
- **Debugging:** Erros silenciados, mensagens genéricas "Erro interno"
- **Logging:** Não consegue distinguir erro de banco vs erro de validação
- **UX:** Usuários recebem mensagens inúteis

### Exemplo Problemático

```python
# ❌ Capturando Exception genérica
@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        # ... lógica ...
        db.session.add(user)
        db.session.commit()
    except:  # Captura TUDO, inclusive bugs!
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar usuário'}), 500
    
    # Resultado: Erro de validação SQL = mesma mensagem que erro de conexão
```

```javascript
// ❌ Try/catch genérico
app.post('/checkout', async (req, res) => {
    try {
        // ... lógica de pagamento ...
    } catch (err) {
        res.status(500).json({ error: 'Erro interno' });
        // Perdemos informação sobre o erro real!
    }
});
```

### Solução ✅

```python
# ✅ Capturar exceções específicas
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        # ... lógica ...
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Email já cadastrado, violação de constraint
        return jsonify({'error': 'Email já cadastrado'}), 409
    except OperationalError:
        db.session.rollback()
        # Erro de conexão com banco
        return jsonify({'error': 'Erro de banco de dados'}), 503
    except Exception as e:
        db.session.rollback()
        # Log do erro real para debugging
        logger.error(f"Erro inesperado ao criar usuário: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500
```

```javascript
// ✅ Discriminar tipos de erro
app.post('/checkout', async (req, res) => {
    try {
        // ... lógica de pagamento ...
    } catch (err) {
        if (err.code === 'PAYMENT_DECLINED') {
            return res.status(400).json({ error: 'Pagamento recusado' });
        } else if (err.code === 'NETWORK_ERROR') {
            return res.status(503).json({ error: 'Serviço de pagamento indisponível' });
        } else {
            logger.error(`Erro inesperado no checkout: ${err.message}`);
            return res.status(500).json({ error: 'Erro interno' });
        }
    }
});
```

### Regras
- ✅ Capture exceções específicas, não genéricas
- ✅ Sempre log do erro real (nunca silenciar)
- ✅ Retorne mensagens diferentes por tipo de erro
- ✅ Use códigos HTTP corretos (409 conflict, 503 service unavailable, etc)
- ✅ Nunca retorne stack trace completo em produção

### Playbook
Veja `refactoring-playbook.md` → **Playbook #9: Exception Handling Robusto**

---

## 10. Validação Inconsistente ou Ausente

**Severidade:** 🟡 MEDIUM  
**Categoria:** Qualidade de Código  
**Frequência:** Alto

### Descrição
Validação de entrada espalhada pelas rotas ou ausente permite dados inválidos, XSS, e comportamento impredizível do sistema.

### Impacto
- **Segurança:** XSS se dados não-sanitizados entram no banco
- **Data Integrity:** Dados inválidos corrompem banco
- **UX:** Operações falham com mensagens genéricas

### Exemplo Problemático

```python
# ❌ Validação espalhada e inconsistente
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    
    if len(title) < 3:  # Validação simples
        return jsonify({'error': 'Título muito curto'}), 400
    if len(title) > 200:
        return jsonify({'error': 'Título muito longo'}), 400
    
    # Mas em outro endpoint...
    @user_bp.route('/users', methods=['POST'])
    def create_user():
        name = data.get('name')
        # Sem validação de comprimento!
        # Sem validação de caracteres especiais!
        # Permite "<script>alert('xss')</script>"
```

### Solução ✅

```python
# ✅ Camada centralizada de validação
from marshmallow import Schema, fields, ValidationError, validate

class TaskSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=3, max=200),
        error_messages={'required': 'Título é obrigatório'}
    )
    description = fields.String(allow_none=True)
    status = fields.String(
        validate=validate.OneOf(['pending', 'in_progress', 'done', 'cancelled']),
        error_messages={'invalid': 'Status inválido'}
    )
    priority = fields.Integer(
        validate=validate.Range(min=1, max=5),
        error_messages={'invalid': 'Prioridade deve ser entre 1 e 5'}
    )
    due_date = fields.DateTime(format='%Y-%m-%d', allow_none=True)

task_schema = TaskSchema()

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        # Validação e deserialização automática
        data = task_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': err.messages}), 400
    
    # Dados garantidamente válidos
    task = Task(**data)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201
```

```javascript
// ✅ Validação com Joi (Node.js)
const Joi = require('joi');

const taskSchema = Joi.object({
    title: Joi.string()
        .min(3)
        .max(200)
        .required()
        .messages({
            'string.empty': 'Título não pode estar vazio',
            'string.min': 'Título deve ter no mínimo 3 caracteres'
        }),
    description: Joi.string().allow(''),
    status: Joi.string()
        .valid('pending', 'in_progress', 'done', 'cancelled')
        .required(),
    priority: Joi.number().min(1).max(5).required(),
    dueDate: Joi.date().iso().allow(null)
});

app.post('/tasks', async (req, res) => {
    const { error, value } = taskSchema.validate(req.body);
    
    if (error) {
        return res.status(400).json({ error: error.details });
    }
    
    // Dados validados
    const task = await Task.create(value);
    res.json(task);
});
```

### Regras
- ✅ Centralizar validação em schemas (Marshmallow, Joi, etc)
- ✅ Validar tipo, tamanho, formato, valores permitidos
- ✅ Sempre sanitizar entrada para XSS (frameworks fazem isso)
- ✅ Retornar mensagens claras de validação
- ✅ Validar em frontend E backend (não confiar em cliente)

### Playbook
Veja `refactoring-playbook.md` → **Playbook #10: Validação Centralizada**

---

## 11. Uso de APIs e Métodos Deprecated

**Severidade:** 🟡 MEDIUM
**Categoria:** Manutenibilidade / Modernização
**Frequência:** Alto em código legado sem manutenção ativa

### Descrição
Chamar funções, métodos ou pacotes que o próprio runtime/framework/biblioteca já marcou como deprecated (descontinuados). O código funciona hoje, mas emite warnings, perde correções de segurança e pode quebrar em uma futura major version — é dívida técnica silenciosa que só aparece quando o upgrade se torna obrigatório.

### Impacto
- **Manutenibilidade:** upgrades de dependência quebram em produção sem aviso prévio
- **Segurança:** APIs deprecated às vezes o são justamente por falhas de segurança (ex.: geração de datas sem timezone, criptografia legada)
- **Confiabilidade:** comportamento pode mudar silenciosamente entre versões antes da remoção definitiva

### Sinais de Detecção
- Grep por chamadas conhecidas como deprecated na stack detectada na Fase 1 (ex.: `datetime.utcnow()` em Python ≥3.12, `@app.before_first_request` em Flask ≥2.3, `new Buffer()` em Node.js, `url.parse()` em favor de `URL`, middleware `body-parser` standalone quando o framework já embute equivalente)
- `DeprecationWarning` / `FutureWarning` no console ao rodar a aplicação ou a suíte de testes
- Versão da dependência no manifesto (`requirements.txt`, `package.json`) mais antiga que a versão mínima recomendada pelo mantenedor (changelog/release notes do pacote)

### Exemplo Problemático

```python
# ❌ Python — datetime.utcnow() é deprecated desde Python 3.12
from datetime import datetime

def registrar_evento():
    return {'timestamp': datetime.utcnow()}  # DeprecationWarning; sem timezone info
```

```javascript
// ❌ Node.js — new Buffer() é deprecated desde Node 6, removido em versões futuras
const dados = new Buffer('conteudo');  // DeprecationWarning: Buffer() is deprecated

// ❌ url.parse() é deprecated em favor da API WHATWG URL
const url = require('url');
const parsed = url.parse(req.url, true);
```

### Solução ✅

```python
# ✅ Python — timezone-aware, API atual
from datetime import datetime, timezone

def registrar_evento():
    return {'timestamp': datetime.now(timezone.utc)}
```

```javascript
// ✅ Node.js — API atual, sem warnings
const dados = Buffer.from('conteudo');

const parsed = new URL(req.url, `http://${req.headers.host}`);
```

### Regras
- ✅ Rodar a aplicação/testes e checar o console por `DeprecationWarning`/`FutureWarning` antes de considerar a Fase 3 concluída
- ✅ Consultar o changelog da versão instalada de cada dependência principal (framework, ORM, driver de banco)
- ✅ Substituir sempre pela API atual equivalente, nunca silenciar o warning
- ✅ Fixar versões no manifesto de dependências (não usar `*`/ranges muito abertos) para evitar deprecations surpresa

### Playbook
Veja `refactoring-playbook.md` → **Playbook #11: Substituir APIs Deprecated**

---

## 12. Magic Numbers e Nomenclatura Pouco Descritiva

**Severidade:** 🔵 LOW
**Categoria:** Legibilidade
**Frequência:** Muito Alto

### Descrição
Valores numéricos ou de string soltos no meio da lógica sem nome que explique seu significado ("magic numbers"), e nomes de variáveis/parâmetros abreviados demais (`u`, `t`, `d`, `cc`) que obrigam quem lê o código a inferir o que representam. Não quebra a aplicação, mas aumenta o tempo de leitura e o risco de erro ao alterar o valor no lugar errado.

### Impacto
- **Legibilidade:** exige contexto externo (ou adivinhação) para entender o código
- **Manutenibilidade:** o mesmo "magic number" costuma ser copiado em vários lugares; mudar a regra de negócio exige achar todas as ocorrências manualmente
- **Onboarding:** aumenta a curva de entrada para novos desenvolvedores no projeto

### Exemplo Problemático

```python
# ❌ Magic numbers e nomes abreviados
def calcular_desconto(p, qtd):
    if qtd > 10:
        return p * 0.85  # o que é 0.85? por que 10?
    return p

for t in tasks:  # t = task, mas só quem escreveu sabe
    if t.priority > 3:  # o que significa prioridade > 3?
        ...
```

```javascript
// ❌ Magic numbers e nomes abreviados
function processarPagamento(cc, e, u) {
    if (cc.length !== 16) { ... }       // por que 16?
    setTimeout(() => reenviar(e), 3600000);  // o que é esse número?
}
```

### Solução ✅

```python
# ✅ Constantes nomeadas e nomes completos
DESCONTO_ATACADO = 0.85
QUANTIDADE_MINIMA_ATACADO = 10

def calcular_desconto(preco, quantidade):
    if quantidade > QUANTIDADE_MINIMA_ATACADO:
        return preco * DESCONTO_ATACADO
    return preco

PRIORIDADE_ALTA = 3

for task in tasks:
    if task.priority > PRIORIDADE_ALTA:
        ...
```

```javascript
// ✅ Constantes nomeadas e nomes completos
const CREDIT_CARD_LENGTH = 16;
const RETRY_DELAY_MS = 60 * 60 * 1000; // 1 hora

function processarPagamento(creditCard, email, user) {
    if (creditCard.length !== CREDIT_CARD_LENGTH) { ... }
    setTimeout(() => reenviar(email), RETRY_DELAY_MS);
}
```

### Regras
- ✅ Extrair valores numéricos/string repetidos ou não-óbvios para constantes nomeadas
- ✅ Nome da constante explica o "porquê", não repete o valor (`QUANTIDADE_MINIMA_ATACADO`, não `DEZ`)
- ✅ Parâmetros e variáveis com nome completo e descritivo (`user`, `task`, `creditCard` em vez de `u`, `t`, `cc`)
- ✅ Exceção aceitável: índices de loop puramente locais (`i`, `j`) em laços curtos e óbvios

### Playbook
Veja `refactoring-playbook.md` → **Playbook #12: Eliminar Magic Numbers e Renomear Variáveis**

---

## Resumo de Severidades

| Anti-Pattern | Severidade | Categoria |
|--------------|-----------|-----------|
| SQL Injection | CRITICAL | Segurança |
| Credenciais Hardcoded | CRITICAL | Segurança |
| Autenticação Ausente | CRITICAL | Segurança |
| Criptografia Fraca | CRITICAL | Segurança |
| N+1 Queries | HIGH | Performance |
| Callback Hell | HIGH | Manutenibilidade |
| Código Duplicado | MEDIUM | Manutenibilidade |
| Variáveis Globais | MEDIUM | Confiabilidade |
| Exception Genérica | MEDIUM | Qualidade |
| Validação Inconsistente | MEDIUM | Qualidade |
| APIs Deprecated | MEDIUM | Manutenibilidade / Modernização |
| Magic Numbers / Nomenclatura | LOW | Legibilidade |

## Próximos Passos

1. Leia `architecture-rules.md` para entender a estrutura esperada
2. Consulte `refactoring-playbook.md` para playbooks passo-a-passo
3. Use `heuristics.md` para validar refatoração
4. Gere relatório com `report-template.md`
