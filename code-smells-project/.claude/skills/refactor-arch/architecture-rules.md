# Architecture Rules & MVC Guidelines

Diretrizes de arquitetura para garantir que refatorações sigam padrões profissionais e escaláveis.

---

## MVC Layer Architecture

A arquitetura ideal segue separação clara de responsabilidades em camadas:

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│              (routes, controllers, middleware)            │
│  ├─ routes/user_routes.py                               │
│  ├─ routes/task_routes.py                               │
│  └─ middleware/auth.py                                  │
├─────────────────────────────────────────────────────────┤
│                    BUSINESS LOGIC LAYER                  │
│           (services, validators, transformers)           │
│  ├─ services/user_service.py                            │
│  ├─ services/task_service.py                            │
│  ├─ validators/task_validator.py                        │
│  └─ utils/helpers.py                                    │
├─────────────────────────────────────────────────────────┤
│                    DATA ACCESS LAYER                     │
│              (models, repositories, ORM)                 │
│  ├─ models/user.py                                      │
│  ├─ models/task.py                                      │
│  ├─ repositories/user_repository.py                     │
│  └─ database.py                                         │
├─────────────────────────────────────────────────────────┤
│                    EXTERNAL LAYER                        │
│           (banco, APIs externas, filesystems)            │
│  └─ SQL/NoSQL Database                                  │
└─────────────────────────────────────────────────────────┘
```

### Fluxo de Requisição

```
1. REQUEST entra na route
   ↓
2. Middleware de autenticação (auth.py)
   ↓
3. Route handler valida entrada (schemas)
   ↓
4. Chama service (business logic)
   ↓
5. Service consulta repository
   ↓
6. Repository usa ORM/models para DB
   ↓
7. Response serializada volta através das camadas
   ↓
8. RESPONSE retorna ao cliente
```

---

## Layer Responsibilities

### 1. Routes Layer (Controller)

**Localização:** `routes/`, `controllers/`  
**Responsabilidade:** HTTP request/response handling

**O que FAZER:**
- ✅ Definir endpoints e métodos HTTP
- ✅ Extrair parâmetros e validar entrada
- ✅ Chamar services apropriados
- ✅ Serializar resposta em JSON
- ✅ Retornar status HTTP correto

**O que NÃO fazer:**
- ❌ Lógica de negócio (ex: calcular totais, gerar relatórios)
- ❌ Queries diretas ao banco
- ❌ Transformação de dados complexa
- ❌ Chamadas a APIs externas
- ❌ Tratamento de arquivo

**Exemplo CORRETO:**

```python
# ✅ routes/task_routes.py
from flask import Blueprint, request, jsonify
from services.task_service import TaskService
from validators.task_validator import TaskValidator

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    # 1. Validar entrada
    try:
        data = TaskValidator.validate_create(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    # 2. Chamar service (lógica de negócio)
    try:
        task = TaskService.create(data, current_user_id)
    except BusinessException as err:
        return jsonify({'error': str(err)}), 400
    
    # 3. Serializar resposta
    return jsonify({
        'data': task.to_dict(),
        'message': 'Task criada com sucesso'
    }), 201
```

**Exemplo INCORRETO:**

```python
# ❌ Lógica de negócio na route
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    # ❌ Query direta no banco
    db.run("INSERT INTO tasks (...) VALUES (...)")
    
    # ❌ Transformação de dados
    tags = ','.join(data['tags'])
    
    # ❌ Validação complexa
    if len(data['title']) < 3:
        # ... mais validações ...
    
    return jsonify({'success': True})
```

---

### 2. Services Layer (Business Logic)

**Localização:** `services/`  
**Responsabilidade:** Lógica de negócio, orquestração

**O que FAZER:**
- ✅ Implementar regras de negócio
- ✅ Orquestrar operações (ex: criar task + enviar email)
- ✅ Validações complexas
- ✅ Transformações de dados
- ✅ Chamar múltiplas repositories
- ✅ Chamar APIs externas
- ✅ Gerenciar transações

**O que NÃO fazer:**
- ❌ Acessar HTTP request/response
- ❌ Retornar JSON (retorna dicts/objects)
- ❌ Query SQL direto (usar repository)
- ❌ Definir rotas
- ❌ Middleware

**Exemplo CORRETO:**

```python
# ✅ services/task_service.py
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from services.notification_service import NotificationService
from exceptions import BusinessException

class TaskService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.user_repo = UserRepository()
        self.notifier = NotificationService()
    
    def create(self, data, user_id):
        """Criar nova task com validações de negócio"""
        
        # Validação de negócio
        if not self.user_repo.exists(user_id):
            raise BusinessException("Usuário não encontrado")
        
        # Criar task via repository
        task = self.task_repo.create({
            **data,
            'user_id': user_id
        })
        
        # Notificação (orquestração)
        self.notifier.send_task_assigned(user_id, task)
        
        return task
    
    def get_user_stats(self, user_id):
        """Gerar estatísticas do usuário"""
        tasks = self.task_repo.find_by_user(user_id)
        
        return {
            'total': len(tasks),
            'completed': len([t for t in tasks if t.status == 'done']),
            'overdue': len([t for t in tasks if t.is_overdue()])
        }
```

---

### 3. Repository Layer (Data Access)

**Localização:** `repositories/`  
**Responsabilidade:** Abstração de acesso a dados

**O que FAZER:**
- ✅ Implementar CRUD básico (create, read, update, delete)
- ✅ Queries complexas (filtros, joins, aggregations)
- ✅ Eager loading de relacionamentos
- ✅ Paginação
- ✅ Cachear se apropriado

**O que NÃO fazer:**
- ❌ Lógica de negócio complexa
- ❌ Transformação de dados (responsabilidade do model)
- ❌ Chamadas a APIs externas
- ❌ HTTP requests

**Exemplo CORRETO:**

```python
# ✅ repositories/task_repository.py
from models.task import Task
from database import db

class TaskRepository:
    def create(self, data):
        task = Task(**data)
        db.session.add(task)
        db.session.commit()
        return task
    
    def find_by_id(self, task_id):
        return Task.query.get(task_id)
    
    def find_by_user(self, user_id, filters=None):
        """Buscar tasks do usuário com eager loading"""
        query = Task.query.filter_by(user_id=user_id)
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
        
        # Eager load de relacionamentos (evita N+1)
        query = query.options(joinedload(Task.user))
        
        return query.all()
    
    def find_all_paginated(self, page=1, per_page=20):
        """Paginação"""
        return Task.query.paginate(page, per_page)
    
    def update(self, task_id, data):
        task = self.find_by_id(task_id)
        if task:
            for key, value in data.items():
                setattr(task, key, value)
            db.session.commit()
        return task
    
    def delete(self, task_id):
        task = self.find_by_id(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
        return True
```

---

### 4. Models Layer (Domain Objects)

**Localização:** `models/`  
**Responsabilidade:** Estrutura de dados, validações de domínio

**Esta camada é obrigatória mesmo sem ORM.** Ela não depende de o projeto usar um ORM (SQLAlchemy, Sequelize, TypeORM) — é sobre existir uma classe de domínio entre o banco e o resto da aplicação. Se o repository usa um driver cru (`sqlite3`, `pg`, `mysql2`) e faz `SELECT *`, a linha crua (`row`) **não pode** ser devolvida direto para o service: o repository deve montar um objeto de domínio (`Model.fromRow(row)`) a partir dela antes de retornar. Sinal de que esta camada está faltando: um repository cujo método de leitura termina em `return this.db.get(...)` / `return this.db.all(...)` sem nenhuma transformação no meio — a assinatura do método promete uma entidade, mas entrega uma linha de banco.

**O que FAZER:**
- ✅ Definir schema do banco (fields, tipos, constraints) — via ORM ou via classe simples (`fromRow`) quando não há ORM
- ✅ Validações de domínio (métodos de negócio)
- ✅ Relacionamentos (foreign keys, backrefs)
- ✅ Serialização (to_dict/to_json, ou toPublicJSON em JS)
- ✅ Métodos de utilidade (is_overdue, is_valid, isAdmin, etc)

**O que NÃO fazer:**
- ❌ SQL queries direto
- ❌ Chamar APIs externas
- ❌ Lógica complexa (ir para service)

**Exemplo CORRETO (com ORM):**

```python
# ✅ models/task.py
from database import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def is_overdue(self):
        """Validação de domínio: task está atrasada?"""
        if not self.due_date:
            return False
        
        if self.due_date >= datetime.utcnow():
            return False
        
        return self.status not in ['done', 'cancelled']
    
    def can_be_deleted(self):
        """Regra de negócio: pode deletar?"""
        return self.status in ['pending', 'cancelled']
```

**Exemplo CORRETO (sem ORM — driver SQL cru, ex.: Node.js + `sqlite3`/`pg`):**

Quando não há ORM, o model é uma classe simples com um construtor + um `fromRow` estático que o repository chama para transformar a linha crua do banco em um objeto de domínio, antes de devolvê-lo ao service.

```javascript
// ✅ models/User.js — classe de domínio, sem ORM
const bcrypt = require('bcrypt');

class User {
    constructor({ id, name, email, pass_hash: passHash, role }) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.passHash = passHash;
        this.role = role;
    }

    // Constrói a entidade a partir de uma linha crua do banco
    static fromRow(row) {
        return row ? new User(row) : null;
    }

    isAdmin() {
        return this.role === 'admin';
    }

    verifyPassword(password) {
        return bcrypt.compare(password, this.passHash);
    }

    // Serialização: nunca inclui passHash
    toPublicJSON() {
        return { id: this.id, name: this.name, email: this.email, role: this.role };
    }
}

module.exports = { User };
```

```javascript
// ✅ repositories/userRepository.js — devolve a entidade, não a linha crua
const { User } = require('../models/User');

class UserRepository {
    constructor(db) {
        this.db = db;
    }

    async findByEmail(email) {
        const row = await this.db.get('SELECT * FROM users WHERE email = ?', [email]);
        return User.fromRow(row);   // ✅ entidade de domínio
    }
}
```

```javascript
// ❌ INCORRETO — repository devolve a linha crua do banco direto para o service
class UserRepository {
    findByEmail(email) {
        return this.db.get('SELECT * FROM users WHERE email = ?', [email]); // ❌ raw row
    }
}
// service agora depende de nomes de coluna do banco (pass_hash) e não tem
// nenhum método de domínio disponível (isAdmin, verifyPassword, etc)
```

---

### 5. Validators Layer (Input Validation)

**Localização:** `validators/`  
**Responsabilidade:** Validação de entrada

**O que FAZER:**
- ✅ Validar tipo, tamanho, formato
- ✅ Validar business rules (ex: email único)
- ✅ Retornar erros estruturados
- ✅ Reutilizar schemas

**O que NÃO fazer:**
- ❌ Lógica de negócio
- ❌ Queries ao banco (isso vai no service)

**Exemplo CORRETO:**

```python
# ✅ validators/task_validator.py
from marshmallow import Schema, fields, validate, ValidationError

class TaskCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=3, max=200)
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

class TaskValidator:
    schema = TaskCreateSchema()
    
    @staticmethod
    def validate_create(data):
        return TaskValidator.schema.load(data)
```

---

## Middleware Layer

**Localização:** `middleware/`  
**Responsabilidade:** Lógica transversal (autenticação, logging, etc)

**Padrão:**

```python
# ✅ middleware/auth.py
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

def login_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        return f(current_user_id, *args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(current_user_id, *args, **kwargs):
        user = User.query.get(current_user_id)
        if user.role != 'admin':
            return jsonify({'error': 'Sem permissão'}), 403
        return f(current_user_id, *args, **kwargs)
    return decorated_function

# Uso:
@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@admin_required
def delete_task(current_user_id, task_id):
    # Garantido: autenticado e admin
    TaskService.delete(task_id)
    return jsonify({'message': 'Deletado'}), 200
```

---

## Project Structure

Organização recomendada (nomes de arquivo/extensão variam por stack — `.py`/`.js`/etc — mas a lista de camadas, incluindo `models/`, é a mesma independentemente de a stack ter ORM ou usar um driver SQL cru):

```
projeto/
├── app.py                          # Inicialização Flask
├── config.py                       # Configurações (dev, test, prod)
├── requirements.txt                # Dependências
├── .env                            # Variáveis de ambiente (NÃO commitar)
├── .gitignore                      # Ignorar .env, __pycache__, etc
│
├── database.py                     # Inicialização SQLAlchemy
│
├── models/                         # Camada de domínio
│   ├── __init__.py
│   ├── user.py
│   ├── task.py
│   └── category.py
│
├── repositories/                   # Camada de dados
│   ├── __init__.py
│   ├── base_repository.py          # Classe base com CRUD
│   ├── user_repository.py
│   ├── task_repository.py
│   └── category_repository.py
│
├── services/                       # Camada de lógica de negócio
│   ├── __init__.py
│   ├── user_service.py
│   ├── task_service.py
│   ├── notification_service.py
│   └── report_service.py
│
├── validators/                     # Validação de entrada
│   ├── __init__.py
│   ├── user_validator.py
│   └── task_validator.py
│
├── routes/                         # Camada de apresentação
│   ├── __init__.py
│   ├── user_routes.py
│   ├── task_routes.py
│   └── report_routes.py
│
├── middleware/                     # Middleware (auth, logging, etc)
│   ├── __init__.py
│   ├── auth.py
│   └── error_handler.py
│
├── utils/                          # Utilitários
│   ├── __init__.py
│   ├── helpers.py
│   └── decorators.py
│
├── exceptions/                     # Custom exceptions
│   ├── __init__.py
│   └── business_exceptions.py
│
└── tests/                          # Testes (unit, integration)
    ├── test_task_service.py
    ├── test_task_routes.py
    └── conftest.py
```

---

## Configuration Management

**Nunca hardcode configurações:**

```python
# ❌ INCORRETO
app.config['DATABASE_URL'] = 'postgresql://user:pass@localhost/db'
app.config['SECRET_KEY'] = 'super-secret-123'
app.config['DEBUG'] = True

# ✅ CORRETO - config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuração base"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-prod')
    JWT_ALGORITHM = 'HS256'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev.db')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Validações de segurança
    if not os.getenv('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY deve estar configurada em produção')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# app.py
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])
```

---

## Security Rules

### Input Validation
- ✅ Sempre validar entrada (tipo, tamanho, conteúdo)
- ✅ Rejeitar dados inválidos com 400 Bad Request
- ✅ Nunca confiar em dados do cliente

### Authentication
- ✅ Todas rotas exceto /login, /register, /health requerem JWT
- ✅ Usar Bearer token nos headers: `Authorization: Bearer <token>`
- ✅ JWT deve expirar em 1 hora (tokens curtos)
- ✅ Refresh tokens para renovação (7-30 dias)

### Authorization
- ✅ Verificar role (user, admin, manager)
- ✅ Verificar propriedade (usuário só acessa dados próprios)
- ✅ Endpoints admin exigem is_admin()

### Data Protection
- ✅ Nunca retornar senhas/hashes em APIs
- ✅ Usar HTTPS em produção (TLS 1.2+)
- ✅ CORS configurado (não allow *)
- ✅ Rate limiting em endpoints sensíveis (login, register)

### Database Security
- ✅ Prepared statements (ORM faz automaticamente)
- ✅ Encriptação de senhas com bcrypt/argon2
- ✅ Backup regular
- ✅ Sem credenciais no código

---

## Performance Rules

### Query Optimization
- ✅ Use eager loading (joinedload, selectinload)
- ✅ Índices em campos frequentemente filtrados
- ✅ Paginação para listas grandes
- ✅ Cache para dados read-heavy (Redis)
- ✅ Async para operações I/O (emails, APIs externas)

### Caching Strategy
- ✅ Cache de read-heavy (ex: relatórios)
- ✅ Invalidar cache quando dados mudam
- ✅ Redis para cache distribuído
- ✅ Nunca cache dados sensíveis (senhas, tokens)

---

## Testing Rules

Cada camada deve ter testes:

```python
# ✅ tests/test_task_service.py - Testes de lógica
def test_task_creation():
    service = TaskService()
    task = service.create({'title': 'Test'}, user_id=1)
    assert task.title == 'Test'

# ✅ tests/test_task_routes.py - Testes de integração
def test_create_task_endpoint(client, auth_header):
    response = client.post('/tasks', 
        json={'title': 'Test'},
        headers=auth_header
    )
    assert response.status_code == 201
```

---

## Dependency Injection

**Usar injeção de dependência para testabilidade:**

```python
# ✅ services/task_service.py
class TaskService:
    def __init__(self, task_repo=None, user_repo=None, notifier=None):
        self.task_repo = task_repo or TaskRepository()
        self.user_repo = user_repo or UserRepository()
        self.notifier = notifier or NotificationService()
    
    def create(self, data, user_id):
        # Código aqui

# Uso em produção
service = TaskService()

# Uso em testes (injetar mocks)
service = TaskService(
    task_repo=MockTaskRepository(),
    user_repo=MockUserRepository(),
    notifier=MockNotificationService()
)
```

---

## Próximos Passos

1. Ler `refactoring-playbook.md` para transformações passo-a-passo
2. Consultar `heuristics.md` para validar conformidade
3. Usar `antipatterns.md` para identificar problemas
