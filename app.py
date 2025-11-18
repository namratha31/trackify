from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from collections import defaultdict
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trackify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'dev-secret'

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    name = db.Column(db.String(100))
    profile_pic = db.Column(db.String(200))
    monthly_income = db.Column(db.Float, default=0.0)
    target_savings = db.Column(db.Float, default=0.0)
    bio = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.now)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category')
    date = db.Column(db.Date, default=date.today)
    note = db.Column(db.String(200))

class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300))
    deadline = db.Column(db.Date, nullable=True)
    progress = db.Column(db.Float, default=0.0)

def ensure_db():
    with app.app_context():
        db.create_all()
        if Category.query.count() == 0:
            for name in ['Salary', 'Groceries', 'Transport', 'Entertainment', 'Utilities', 'Other']:
                db.session.add(Category(name=name))
            db.session.commit()

@app.before_request
def load_user():
    user_id = session.get('user_id')
    g.user = User.query.get(user_id) if user_id else None

# Initialize database on app startup
with app.app_context():
    try:
        # Drop all old tables and recreate fresh
        db.drop_all()
    except:
        pass
    db.create_all()
    # Seed categories
    if Category.query.count() == 0:
        for name in ['Salary', 'Groceries', 'Transport', 'Entertainment', 'Utilities', 'Other']:
            db.session.add(Category(name=name))
        db.session.commit()
    print("✓ Database initialized successfully")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash('Please login', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        
        if not username or not password or not email:
            flash('Username, password, and email are required', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
        else:
            user = User(username=username, password=generate_password_hash(password), email=email, name=username)
            db.session.add(user)
            db.session.commit()
            flash('✓ Signup successful! Please login now.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'danger')
        else:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session.clear()
                session['user_id'] = user.id
                flash(f'✓ Welcome {user.name}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('❌ Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    ensure_db()
    transactions = Transaction.query.filter_by(user_id=g.user.id).order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expense
    recent = transactions[:8]
    expenses = [t for t in transactions if t.type == 'expense']
    cat_sums = {}
    for t in expenses:
        name = t.category.name if t.category else 'Uncategorized'
        cat_sums[name] = cat_sums.get(name, 0) + t.amount
    monthly = defaultdict(float)
    for t in transactions:
        key = t.date.strftime('%Y-%m')
        monthly[key] += t.amount if t.type == 'income' else -t.amount
    months = sorted(monthly.keys())[-6:]
    month_vals = [monthly[m] for m in months]
    # Get user's goals
    goals = SavingsGoal.query.filter_by(user_id=g.user.id).all()
    return render_template('index.html', total_income=total_income, total_expense=total_expense, balance=balance, recent=recent, cat_sums=cat_sums, months=months, month_vals=month_vals, goals=goals, user=g.user)

@app.route('/transactions')
@login_required
def transactions():
    ensure_db()
    txs = Transaction.query.filter_by(user_id=g.user.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=txs)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    ensure_db()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        try:
            amt = float(request.form['amount'])
            ttype = request.form['type']
            cat_id = request.form.get('category')
            note = request.form.get('note')
            date_str = request.form.get('date')
            dt = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
            if cat_id == 'new':
                new_cat_name = request.form.get('new_category', '').strip()
                cat = Category.query.filter_by(name=new_cat_name).first() if new_cat_name else None
                if new_cat_name and not cat:
                    cat = Category(name=new_cat_name)
                    db.session.add(cat)
                    db.session.commit()
            else:
                cat = Category.query.get(int(cat_id)) if cat_id else None
            tx = Transaction(user_id=g.user.id, amount=amt, type=ttype, category=cat, note=note, date=dt)
            db.session.add(tx)
            db.session.commit()
            flash('Added!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('add_transaction.html', categories=categories)

@app.route('/delete/<int:tx_id>', methods=['POST'])
@login_required
def delete(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, user_id=g.user.id).first_or_404()
    db.session.delete(tx)
    db.session.commit()
    flash('Deleted', 'info')
    return redirect(request.referrer or url_for('transactions'))

@app.route('/api/category_breakdown')
@login_required
def api_category_breakdown():
    expenses = Transaction.query.filter_by(user_id=g.user.id, type='expense').all()
    data = {}
    for t in expenses:
        name = t.category.name if t.category else 'Uncategorized'
        data[name] = data.get(name, 0) + t.amount
    return jsonify(data)

@app.route('/insights')
@login_required
def insights():
    ensure_db()
    transactions = Transaction.query.filter_by(user_id=g.user.id).order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    monthly_income = g.user.monthly_income if g.user.monthly_income > 0 else (total_income / (len(set(t.date.strftime('%Y-%m') for t in transactions)) or 1))
    savings_rate = ((monthly_income - total_expense) / monthly_income * 100) if monthly_income else 0
    expenses_by_category = {}
    for t in transactions:
        if t.type == 'expense':
            cat_name = t.category.name if t.category else 'Uncategorized'
            expenses_by_category[cat_name] = expenses_by_category.get(cat_name, 0) + t.amount
    sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
    tips = []
    if savings_rate < 20:
        tips.append({'type': 'warning', 'title': 'Increase Savings', 'description': 'Aim for 20% savings rate'})
    else:
        tips.append({'type': 'success', 'title': 'Great!', 'description': f'Saving {savings_rate:.1f}%'})
    savings_goals = [
        {'title': 'Emergency Fund', 'target': monthly_income * 6, 'priority': 'High'},
        {'title': 'Retirement', 'target': monthly_income * 12, 'priority': 'Medium'},
        {'title': 'Short-term', 'target': monthly_income * 3, 'priority': 'Low'}
    ]
    user_goals = SavingsGoal.query.filter_by(user_id=g.user.id).all()
    return render_template('insights.html', savings_rate=savings_rate, tips=tips, savings_goals=savings_goals, user_goals=user_goals, categories=sorted_categories, user=g.user, monthly_income=monthly_income)

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        try:
            target = float(request.form.get('target_amount', 0))
        except:
            target = 0
        if name and target > 0:
            goal = SavingsGoal(user_id=g.user.id, name=name, target_amount=target, description=request.form.get('description'))
            db.session.add(goal)
            db.session.commit()
            flash('Goal added!', 'success')
            return redirect(url_for('goals'))
    goals = SavingsGoal.query.filter_by(user_id=g.user.id).all()
    return render_template('goals.html', goals=goals)

@app.route('/goals/edit/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=g.user.id).first_or_404()
    if request.method == 'POST':
        goal.name = request.form.get('name', '').strip() or goal.name
        try:
            goal.target_amount = float(request.form.get('target_amount') or goal.target_amount)
        except:
            pass
        try:
            goal.progress = float(request.form.get('progress') or goal.progress)
        except:
            pass
        goal.description = request.form.get('description', '').strip() or goal.description
        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                goal.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except:
                pass
        db.session.commit()
        flash('✓ Goal updated!', 'success')
        return redirect(url_for('goals'))
    return render_template('edit_goal.html', goal=goal)

@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=g.user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash('Deleted!', 'info')
    return redirect(url_for('goals'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        g.user.name = request.form.get('name', '').strip() or g.user.name
        g.user.email = request.form.get('email', '').strip() or None
        try:
            g.user.monthly_income = float(request.form.get('monthly_income') or 0)
        except:
            pass
        g.user.bio = request.form.get('bio', '').strip()
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename:
                filename = secure_filename(f"{g.user.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                g.user.profile_pic = filename
        db.session.commit()
        flash('Saved!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=g.user)

if __name__ == '__main__':
    print(' Trackify running on http://127.0.0.1:8080')
    app.run(debug=True, host='127.0.0.1', port=8080)
