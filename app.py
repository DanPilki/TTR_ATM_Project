from flask import Flask, render_template, redirect, url_for, request, flash
import sqlite3
app = Flask(__name__)
app.secret_key = 'secretkey123'
# data goes from POST from web page > application > database > then changed and restored there


class Account:
    def __init__(self, checking_amt, savings_amt, pin):
        self.checking_amt = checking_amt
        self.savings_amt = savings_amt
        self.pin = pin


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # load the DB pins to reference the incoming login request
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("SELECT pin FROM accounts")
        all_pins = c.fetchall()
        str_list = []
        all_pins = list(all_pins)
        for x in range(len(all_pins)):
            # convert all of the tuple from the query into ints
            temp = str(all_pins[x])[2:-3]
            str_list.append(temp)
        # receive post
        c.close()
        pin_entry = request.form['pin']
        for x in range(len(str_list)):
            if pin_entry == str_list[x]:
                # if the pin entry is in the DB column for pins, load that profile
                return redirect(url_for('acctinfo', pin_passed=pin_entry))
            error = 'Invalid Pin, please try again'
    return render_template('login.html', error=error)


@app.route('/acctinfo/<string:pin_passed>')
def acctinfo(pin_passed):
    # where the SQL commands that pull up a particular pins info will go
    # open the DB
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # select the acct info from the pin that is sent from login screen
    c.execute("SELECT checking FROM accounts WHERE pin = ?", (pin_passed,))
    checking = c.fetchone()
    c.execute("SELECT savings FROM accounts WHERE pin = ?", (pin_passed,))
    savings = c.fetchone()

    # close db connection
    c.close()
    # convert db selects from tuple to int/double
    checking_str = str(checking)[1:-2]
    savings_str = str(savings)[1:-2]
    checking_int = float(checking_str)
    savings_int = float(savings_str)

    return render_template('acctinfo.html', check=checking_int, save=savings_int, pin=pin_passed)


@app.route('/createacct', methods=['GET', 'POST'])
def createacct():
    error = None
    if request.method == 'POST':
        # create the new pin for the registration
        pin_entered = request.form['pin_entry']
        input_length = len(pin_entered)
        if input_length > 8 or input_length < 4:
            error = "Pin entered is not in the required character range, please try again"
            return render_template('createacct.html', error=error)
        check = '0'
        savings = '0'
        int_check = int(check)
        int_savings = int(savings)
        # check to make sure pin is unique
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("SELECT pin FROM accounts")
        all_pins = c.fetchall()
        str_list = []
        all_pins = list(all_pins)
        for x in range(len(all_pins)):
            # convert all of the tuple from the query into ints
            temp = str(all_pins[x])[2:-3]
            temp1 = int(temp)
            str_list.append(temp)
        print(str_list)
        for x in range(len(str_list)):
            if pin_entered == str_list[x]:
                error = "pin already exists, please choose a unique pin"
                conn.close()
                return render_template('createacct.html', error=error)
        # send new pin to the database with 0 balance
        c.execute("INSERT INTO accounts (pin, checking, savings) VALUES (?, ?, ?)"
                  , (pin_entered, int_check, int_savings,))
        conn.commit()
        conn.close()
        flash('Pin created')
        return redirect(url_for('login'))
    return render_template('createacct.html', error=error)

# needed for 405 HTTP error handling, the checking and savings info needs to have a default value
@app.route('/deposit/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>'
           , defaults={'checking_amt': 0, 'savings_amt': 0})
@app.route("/deposit/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>", methods=['POST'])
def deposit(pin_passed, checking_amt, savings_amt):
    error = None
    if request.method == 'POST':
        # save the deposit amount into a local variable
        deposit_amt = request.form['deposit_amt']
        add_amt = float(deposit_amt)

        # make sure that its greater than zero
        if deposit_amt < '0':
            error = "Cant Deposit Negative Money"
            return render_template('deposit.html', pin=pin_passed, error=error)
        else:
            conn = sqlite3.connect("data.db")
            c = conn.cursor()
            # if statements check which account the user wants to deposit into
            if request.form['acct_choice'] == 'checking_acct':
                new_amt_check = checking_amt + add_amt
                c.execute("UPDATE accounts SET checking = ? WHERE pin = ?", (new_amt_check, pin_passed))
                conn.commit()
                conn.close()
                return redirect(url_for('acctinfo', pin_passed=pin_passed))
            if request.form['acct_choice'] == 'savings_acct':
                new_amt_save = savings_amt + add_amt
                c.execute("UPDATE accounts SET savings = ? WHERE pin = ?", (new_amt_save, pin_passed))
                conn.commit()
                conn.close()
                return redirect(url_for('acctinfo', pin_passed=pin_passed))
    return render_template('deposit.html', pin=pin_passed, error=error)


@app.route('/withdraw/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>'
           , defaults={'checking_amt': 0, 'savings_amt': 0})
@app.route("/withdraw/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>", methods=['GET', 'POST'])
def withdraw(pin_passed, checking_amt, savings_amt):
    error = None
    if request.method == 'POST':
        withdraw_amt = request.form['withdraw_amt']
        sub_amt = float(withdraw_amt)
        if sub_amt < 0:
            error = "Cannot withdraw negative money cheating swine"
            return render_template('withdraw.html', pin=pin_passed, check=checking_amt, save=savings_amt, error=error)
        else:
            conn = sqlite3.connect("data.db")
            c = conn.cursor()
            # if statements check which account the user wants to deposit into
            if request.form['acct_choice'] == 'checking_acct':
                new_amt_check = checking_amt - sub_amt
                # check to make sure that user doesnt overdraw
                if new_amt_check < 0:
                    error = "Overdraw Alert: unable to complete transaction"
                    return render_template('withdraw.html', pin=pin_passed, check=checking_amt, save=savings_amt,
                                           error=error)
                else:
                    c.execute("UPDATE accounts SET checking = ? WHERE pin = ?", (new_amt_check, pin_passed))

                    # inputs the new amount to the acct info page when it reloads
                    c.execute("SELECT checking FROM accounts WHERE pin = ?", (pin_passed,))
                    new_check_bal = c.fetchone()
                    new_check_bal = str(new_check_bal)[1:-2]
                    new_check_bal = float(new_check_bal)
                    conn.commit()
                    conn.close()
                    return redirect(url_for('acctinfo', pin_passed=pin_passed,
                                            check=new_check_bal, save=savings_amt, error=error))
            if request.form['acct_choice'] == 'savings_acct':
                new_amt_save = savings_amt - sub_amt
                # check to make sure that user doesnt overdraw
                if new_amt_save < 0:
                    error = "Overdraw Alert: unable to complete transaction"
                    return render_template('withdraw.html', pin=pin_passed, check=checking_amt, save=savings_amt,
                                           error=error)
                else:
                    c.execute("UPDATE accounts SET savings = ? WHERE pin = ?", (new_amt_save, pin_passed))
                    c.execute("SELECT savings FROM accounts WHERE pin = ?", (pin_passed,))
                    new_save_bal = c.fetchone()
                    new_save_bal = str(new_save_bal)[1:-2]
                    new_save_bal = float(new_save_bal)
                    conn.commit()
                    conn.close()
                    return redirect(url_for('acctinfo', pin_passed=pin_passed,
                                            check=checking_amt, save=new_save_bal, error=error))
    return render_template('withdraw.html', pin=pin_passed, check=checking_amt, save=savings_amt, error=error)


@app.route('/transfer/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>'
           , defaults={'checking_amt': 0, 'savings_amt': 0})
@app.route("/transfer/<string:pin_passed>/<float:checking_amt>/<float:savings_amt>", methods=['GET', 'POST'])
def transfer(pin_passed, checking_amt, savings_amt):
    error = None
    if request.method == 'POST':
        transfer_amt = request.form['transfer_amt']
        transfer_amt_float = float(transfer_amt)
        if transfer_amt_float < 0:
            error = 'Cannot transfer a negative number'
        else:
            # open db connection
            conn = sqlite3.connect("data.db")
            c = conn.cursor()

            # see which account they wanna transfer to and from
            if request.form['acct_choice'] == 'c_to_s':
                new_checking = checking_amt - transfer_amt_float
                new_savings = savings_amt + transfer_amt_float
                # check to make sure that the account has enough moolah
                if new_checking < 0:
                    error = 'Overdraw on your checking account, not enough balance to complete transfer'
                    return render_template('transfer.html', pin=pin_passed, checking=checking_amt, saving=savings_amt,
                                           error=error)
                else:
                    # db stuff
                    c.execute("UPDATE accounts SET savings = ?, checking = ? WHERE pin = ?",
                              (new_savings, new_checking, pin_passed,))
                    c.execute("SELECT savings FROM accounts WHERE pin = ?", (pin_passed,))
                    temp_saving = c.fetchone()
                    c.execute("SELECT checking FROM accounts WHERE pin = ?", (pin_passed,))
                    temp_checking = c.fetchone()
                    conn.commit()
                    conn.close()
                    # format the DB data
                    temp_saving = str(temp_saving)[1:-2]
                    temp_saving = float(temp_saving)
                    temp_checking = str(temp_checking)[1:-2]
                    temp_checking = float(temp_checking)
                    return render_template('acctinfo.html', pin=pin_passed, check=temp_checking, save=temp_saving,
                                           error=error)
            if request.form['acct_choice'] == 's_to_c':
                new_checking = checking_amt + transfer_amt_float
                new_savings = savings_amt - transfer_amt_float
                # check to make sure that the account has enough moolah
                if new_savings < 0:
                    error = 'Overdraw on your savings account, not enough balance to complete transfer'
                    return render_template('transfer.html', pin=pin_passed, checking=checking_amt, saving=savings_amt,
                                           error=error)
                else:
                    # db stuff
                    c.execute("UPDATE accounts SET savings = ?, checking = ? WHERE pin = ?",
                              (new_savings, new_checking, pin_passed,))
                    c.execute("SELECT savings FROM accounts WHERE pin = ?", (pin_passed,))
                    temp_saving = c.fetchone()
                    c.execute("SELECT checking FROM accounts WHERE pin = ?", (pin_passed,))
                    temp_checking = c.fetchone()
                    conn.commit()
                    conn.close()
                    # format the DB data
                    temp_saving = str(temp_saving)[1:-2]
                    temp_saving = float(temp_saving)
                    temp_checking = str(temp_checking)[1:-2]
                    temp_checking = float(temp_checking)
                    return render_template('acctinfo.html', pin=pin_passed, check=temp_checking, save=temp_saving,
                                           error=error)
    return render_template('transfer.html', pin=pin_passed, checking=checking_amt, saving=savings_amt, error=error)


if __name__ == '__main__':
    app.run(debug=True)
