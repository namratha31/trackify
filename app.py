from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trackify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('TRACKIFY_SECRET', 'dev-secret')

db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Category {self.name}>"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category')
    date = db.Column(db.Date, default=date.today)
    note = db.Column(db.String(200))

    def __repr__(self):
        return f"<Tx {self.id} {self.type} {self.amount}>"


def ensure_db():
    if not os.path.exists('trackify.db'):
        # Ensure DB creation and seeding happen inside the Flask application context
        with app.app_context():
            db.create_all()
            # seed with a few categories
            for name in ['Salary', 'Groceries', 'Transport', 'Entertainment', 'Utilities', 'Other']:
                c = Category(name=name)
                db.session.add(c)
            db.session.commit()


@app.route('/')
def index():
    ensure_db()
    # totals
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expense

    # recent
    recent = transactions[:8]

    # category breakdown for expenses
    expenses = [t for t in transactions if t.type == 'expense']
    cat_sums = {}
    for t in expenses:
        name = t.category.name if t.category else 'Uncategorized'
        cat_sums[name] = cat_sums.get(name, 0) + t.amount

    # monthly series (last 6 months)
    from collections import defaultdict
    monthly = defaultdict(float)
    for t in transactions:
        key = t.date.strftime('%Y-%m')
        monthly[key] += t.amount if t.type == 'income' else -t.amount

    # get last 6 months in order
    months = sorted(monthly.keys())[-6:]
    month_vals = [monthly[m] for m in months]

    return render_template('index.html', total_income=total_income, total_expense=total_expense,
                           balance=balance, recent=recent, cat_sums=cat_sums,
                           months=months, month_vals=month_vals)


@app.route('/transactions')
def transactions():
    ensure_db()
    txs = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=txs)


@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    ensure_db()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        try:
            amt = float(request.form['amount'])
            ttype = request.form['type']
            cat_id = request.form.get('category') or None
            note = request.form.get('note')
            date_str = request.form.get('date')
            if date_str:
                dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                dt = date.today()

            if cat_id == 'new':
                new_cat_name = request.form.get('new_category', '').strip()
                if new_cat_name:
                    cat = Category.query.filter_by(name=new_cat_name).first()
                    if not cat:
                        cat = Category(name=new_cat_name)
                        db.session.add(cat)
                        db.session.commit()
                else:
                    cat = None
            else:
                cat = Category.query.get(int(cat_id)) if cat_id else None

            tx = Transaction(amount=amt, type=ttype, category=cat, note=note, date=dt)
            db.session.add(tx)
            db.session.commit()
            flash('Transaction added', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')

    return render_template('add_transaction.html', categories=categories)


@app.route('/delete/<int:tx_id>', methods=['POST'])
def delete(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    db.session.delete(tx)
    db.session.commit()
    flash('Deleted', 'info')
    return redirect(request.referrer or url_for('transactions'))


@app.route('/api/category_breakdown')
def api_category_breakdown():
    ensure_db()
    expenses = Transaction.query.filter_by(type='expense').all()
    data = {}
    for t in expenses:
        name = t.category.name if t.category else 'Uncategorized'
        data[name] = data.get(name, 0) + t.amount
    return jsonify(data)


if __name__ == '__main__':
    ensure_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
