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


class Profile(db.Model):
    """Simple single-user profile to store basic info and monthly income/targets."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=True)
    monthly_income = db.Column(db.Float, default=0.0)
    target_savings = db.Column(db.Float, default=0.0)
    from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
    from flask_sqlalchemy import SQLAlchemy
    from datetime import datetime, date
    from collections import defaultdict
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


    class Profile(db.Model):
        """Simple single-user profile to store basic info and monthly income/targets."""
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100))
        email = db.Column(db.String(120), unique=True, nullable=True)
        monthly_income = db.Column(db.Float, default=0.0)
        target_savings = db.Column(db.Float, default=0.0)
        bio = db.Column(db.String(300))

        def __repr__(self):
            return f"<Profile {self.name or 'Unnamed'}>"


    def ensure_db():
        """Create DB and seed categories & a default profile if DB doesn't exist."""
        if not os.path.exists('trackify.db'):
            with app.app_context():
                db.create_all()
                # seed categories if empty
                if Category.query.count() == 0:
                    for name in ['Salary', 'Groceries', 'Transport', 'Entertainment', 'Utilities', 'Other']:
                        c = Category(name=name)
                        db.session.add(c)
                    db.session.commit()
                # seed a default profile for single-user flow
                if Profile.query.count() == 0:
                    p = Profile(name='Your Name', email=None, monthly_income=0.0, target_savings=0.0, bio='')
                    db.session.add(p)
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


    @app.route('/insights')
    def insights():
        ensure_db()
        # Calculate spending patterns
        transactions = Transaction.query.order_by(Transaction.date.desc()).all()
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')

        # savings rate (we'll compute using monthly income estimate)
        # prefer profile monthly_income if user provided one
        profile = Profile.query.first()
        if profile and profile.monthly_income and profile.monthly_income > 0:
            monthly_income = profile.monthly_income
        else:
            months_present = len(set(t.date.strftime('%Y-%m') for t in transactions)) or 1
            monthly_income = total_income / months_present

        savings_rate = ((monthly_income - total_expense) / monthly_income * 100) if monthly_income else 0

        # Get category-wise spending
        expenses_by_category = {}
        for t in transactions:
            if t.type == 'expense':
                cat_name = t.category.name if t.category else 'Uncategorized'
                expenses_by_category[cat_name] = expenses_by_category.get(cat_name, 0) + t.amount

        # Sort categories by amount
        sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)

        # Generate personalized tips based on spending patterns
        tips = []
        if savings_rate < 20:
            tips.append({
                'type': 'warning',
                'title': 'Increase Your Savings',
                'description': 'Aim to save at least 20% of your income. Try the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings.'
            })
        else:
            tips.append({
                'type': 'success',
                'title': 'Great Saving Habits!',
                'description': f"You're saving {savings_rate:.1f}% of your income. Keep up the good work!"
            })

        if sorted_categories:
            highest_expense_cat = sorted_categories[0][0]
            tips.append({
                'type': 'info',
                'title': f'High {highest_expense_cat} Spending',
                'description': f'Your highest expense category is {highest_expense_cat}. Consider setting a budget limit for this category.'
            })

        # Monthly comparison (current vs previous month)
        now = datetime.now()
        current_month_expenses = sum(t.amount for t in transactions if t.type == 'expense' and t.date.month == now.month and t.date.year == now.year)
        # previous month handling (wrap year)
        prev_month = (now.month - 1) or 12
        prev_year = now.year if now.month > 1 else now.year - 1
        last_month_expenses = sum(t.amount for t in transactions if t.type == 'expense' and t.date.month == prev_month and t.date.year == prev_year)

        if current_month_expenses > last_month_expenses and last_month_expenses > 0:
            tips.append({
                'type': 'warning',
                'title': 'Spending Trend Alert',
                'description': 'Your spending this month is higher than last month. Review your expenses to stay on track.'
            })

        # Generate savings goals based on monthly_income estimate
        savings_goals = [
            {
                'title': 'Emergency Fund',
                'target': monthly_income * 6,
                'description': 'Aim to save 6 months of expenses for emergencies.',
                'priority': 'High'
            },
            {
                'title': 'Retirement Fund',
                'target': monthly_income * 12,
                'description': 'Start building your retirement savings early.',
                'priority': 'Medium'
            },
            {
                'title': 'Short-term Savings',
                'target': monthly_income * 3,
                'description': 'Save for short-term goals like vacations or purchases.',
                'priority': 'Low'
            }
        ]

        # Money-saving challenges
        challenges = [
            {
                'title': '52-Week Challenge',
                'description': "Save $1 in week 1, $2 in week 2, and so on. You'll have $1,378 by the end of the year!",
                'difficulty': 'Easy'
            },
            {
                'title': 'No-Spend Days',
                'description': 'Challenge yourself to have 2 no-spend days each week.',
                'difficulty': 'Medium'
            },
            {
                'title': '1% Improvement',
                'description': 'Try to reduce each category of spending by 1% each month.',
                'difficulty': 'Hard'
            }
        ]

        return render_template('insights.html', 
                             savings_rate=savings_rate,
                             tips=tips,
                             savings_goals=savings_goals,
                             challenges=challenges,
                             categories=sorted_categories,
                             profile=profile,
                             monthly_income=monthly_income)


    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        ensure_db()
        profile = Profile.query.first()
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip() or None
            try:
                monthly_income = float(request.form.get('monthly_income') or 0)
            except ValueError:
                monthly_income = 0.0
            try:
                target_savings = float(request.form.get('target_savings') or 0)
            except ValueError:
                target_savings = 0.0
            bio = request.form.get('bio', '').strip()

            if not profile:
                profile = Profile(name=name, email=email, monthly_income=monthly_income, target_savings=target_savings, bio=bio)
                db.session.add(profile)
            else:
                profile.name = name
                profile.email = email
                profile.monthly_income = monthly_income
                profile.target_savings = target_savings
                profile.bio = bio

            db.session.commit()
            flash('Profile saved', 'success')
            return redirect(url_for('profile'))

        return render_template('profile.html', profile=profile)


    if __name__ == '__main__':
        print("\n🚀 Starting Trackify - Personal Finance Tracker")
        print("\nMake sure you have:")
        print("1. Activated your virtual environment (.venv)")
        print("2. Installed requirements (pip install -r requirements.txt)")
        print("\nServer Details:")
        print("- URL: http://127.0.0.1:8080")
        print("- Debug Mode: Enabled")
        print("- Database: SQLite (trackify.db)")
        print("\nPress Ctrl+C to stop the server\n")
    
        app.run(debug=True, host='127.0.0.1', port=8080)
