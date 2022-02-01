import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import datetime
from pathlib import Path
import sqlite3
from sqlite3 import Connection
import datetime
import pandas_datareader.data as web
import quandl
from datetime import timedelta


URI_SQLITE_DB = "bdd.db"
QUANDL_API_KEY = 'BCzkk3NDWt7H9yjzx-DY' 
quandl.ApiConfig.api_key = QUANDL_API_KEY
@st.cache
def get_data():
	instruments = pd.read_html('https://en.wikipedia.org/wiki/List_of_S'
					'%26P_500_companies')[0]
	instruments.drop('CIK', axis=1).set_index('Symbol')
	return instruments.drop('SEC filings', axis=1).set_index('Symbol')

@st.cache()
def load_quotes(asset, start, end):
	return yf.download(asset, start, end)

def home():
	instruments = get_data()
	title = st.empty()
	st.sidebar.title("Options")
	st.subheader('Details')

	def label(symbol):
		mnemonic = instruments.loc[symbol]
		return symbol + ' - ' + mnemonic.Security

	if st.sidebar.checkbox('View companies list'):
		st.dataframe(instruments[['Security',
		'GICS Sector',
		'Date first added',
		'Founded']])
	st.sidebar.subheader('Select asset')
	asset = st.sidebar.multiselect('Click below to select a new asset',
	instruments.index.sort_values(), format_func=label)
	start = st.date_input('Start', value = pd.to_datetime('2022-01-01'))
	end = st.date_input('End', value = pd.to_datetime('today'))
	if start > end:
		st.sidebar.error('Error: End date must fall after start date.')
	if len(asset) == 0:
		title.title('Select an instrument')
	else:
		title.title('Overview of '+ str(asset))

	if st.sidebar.checkbox('View company info', False):
		st.table(instruments[['Security','GICS Sector','Date first added',
		'Founded']].loc[asset])
	if len(asset) == 1:
		data0 = load_quotes(''.join(str(asset)[2:-2]), start, end)
		one_year_ago = load_quotes(''.join(str(asset)[2:-2]), pd.to_datetime('today') - pd.DateOffset(years=1, days =10), pd.to_datetime('today') - pd.DateOffset(years=1))
		one_year_ago = one_year_ago.copy().dropna()
		one_year_ago.index.name = None
		one_year_ago = one_year_ago['Adj Close'].iloc[-1]
		data = data0.copy().dropna()
		data.index.name = None
		data2 = data['Adj Close'].to_frame('Adj Close')
		st.line_chart(data2)
		st.write("Rendement de l’action sur 1 an : " + str( \
			round((data['Adj Close'].iloc[-1] - one_year_ago) / one_year_ago * 100, 2)) + "%")
	elif len(asset) > 1:
		data0 = load_quotes(''.join(str(asset).replace('[','').replace(']','').replace('\'','')), start, end)
		data = data0.copy().dropna()
		data.index.name = None
		data2 = data['Adj Close']
		st.line_chart(data2)
		data3 = data['Adj Close'].iloc[-1]
		for elem, instr in zip(data3.tolist(), asset):
			one_year_ago = load_quotes(instr, pd.to_datetime('today') - pd.DateOffset(years=1, days =10), pd.to_datetime('today') - pd.DateOffset(years=1))
			one_year_ago = one_year_ago.copy().dropna()
			one_year_ago.index.name = None
			one_year_ago = one_year_ago['Adj Close'].iloc[-1]
			st.write("Rendement de l’action "+instr+" sur 1 an : " + str( \
				round((elem - one_year_ago) / one_year_ago * 100, 2)) + "%")

	if st.sidebar.checkbox('View statistics'):
		st.subheader('Statistics')
		st.table(data2.describe())

	if st.sidebar.checkbox('View previous closes') and len(asset) > 0:
		st.subheader(f'{asset} Historical data')
		st.write(data2)

def init_db(conn: Connection):
    conn.executescript(
        """  
        CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        balance INT,
        creation_date DATETIME
        
        );
        
        CREATE TABLE IF NOT EXISTS orders
            (
                  id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                  ticker TEXT,
                  order_type TEXT,
				  price INT,
				  quantity INT, 
                  side TEXT, 
                  date TEXT, 
                  user_id INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(id)

            );
  
            """       
    )

@st.cache(hash_funcs={Connection: id})
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)  
  #affichage des données  
def display_data_user(conn: Connection):
    if st.checkbox("Display user list"):
        st.dataframe(get_read_data_users(conn))
def display_data_ordre(conn: Connection):
    if st.checkbox("Display datas"):
        st.dataframe(get_read_data_ordre(conn))
        
 #recuperation en base       
def get_read_data_users(conn: Connection):
 	df2 = pd.read_sql("SELECT * FROM users", con=conn) 
 	return df2

def get_read_data_ordre(conn: Connection):
	prenom=st.session_state['pseudo'].split()[0]
	nom=st.session_state['pseudo'].split()[1]
	curseur=conn.execute("select id from users where name=? and first_name=? " , [nom, prenom])
	id_user = curseur.fetchone()[0]
	sql_crawled = 'select * from orders where user_id=%s' % (id_user)
	df = pd.read_sql_query(sql_crawled, con=conn)
	return df
def signup():
	conn = get_connection(URI_SQLITE_DB)
	if 'pseudo' not in st.session_state.keys():
		with st.form('Sign up'):
			st.title("Sign up")
			prenom=st.text_input(label='First Name')
			if not prenom:
				st.warning('Please fill this field.')
			nom=st.text_input(label='Last Name')
			if not nom:
				st.warning('Please fill this field.')
			capital=st.slider(label='Balance', min_value=0, max_value=100000, key=10)
			creation_date = datetime.date.today()
			submitted = st.form_submit_button('Validate')
			if submitted != 0 and len(prenom) > 0 and len(nom) > 0:
				st.write(f'Welcome {nom}')
				conn.execute("INSERT INTO users (name, first_name, balance,creation_date ) VALUES (?,?,?,?)", [nom, prenom,capital, creation_date])
				st.session_state['pseudo'] = prenom+' '+nom
				conn.commit()
				st.experimental_rerun()
	else:
		st.title('You are connected as '+st.session_state['pseudo'])
		prenom=st.session_state['pseudo'].split()[0]
		nom=st.session_state['pseudo'].split()[1]
		cash=st.slider(label='Do you want to add money ? ', min_value=10, max_value=100000, key=10)
		add = st.button('Add')
		if add:
			conn.execute("UPDATE users SET balance=balance + ? where name=?  and first_name=?", [cash, nom, prenom])
		disconnect = st.button('Disconnect')
		if disconnect:
			del st.session_state['pseudo']
			st.experimental_rerun()
	display_data_user(conn)

def connect():
	conn = get_connection(URI_SQLITE_DB)
	res = get_read_data_users(conn)
	if 'pseudo' not in st.session_state.keys():	
		with st.form('Sign in'):	
			prenom=st.text_input(label='First Name')
			if not prenom:
				st.warning('Please fill this field.')
			nom=st.text_input(label='Last Name')
			if not nom:
				st.warning('Please fill this field.')
			submitted = st.form_submit_button('Connect')
			if submitted != 0 and len(prenom) > 0 and len(nom) > 0:
				if prenom in res['first_name'].tolist() and nom in res['name'].tolist():
					st.session_state['pseudo'] = prenom+' '+nom
					st.experimental_rerun()
				else:
					st.error('User not found')
					if st.form_submit_button('Retry'):
						st.experimental_rerun()	
	else:
		st.title('Already connected')
def orders():
	def label(symbol):
		mnemonic = instruments.loc[symbol]
		return symbol + ' - ' + mnemonic.Security

	def prev_weekday(adate):
		adate -= timedelta(days=1)
		while adate.weekday() > 4: # Mon-Fri are 0-4
			adate -= timedelta(days=1)
		return adate

	if 'pseudo' in st.session_state.keys():
		conn = get_connection(URI_SQLITE_DB)
		type_cours = st.radio("Select multi or simple order",('Unique', 'Multiple'))
		prenom=st.session_state['pseudo'].split()[0]
		nom=st.session_state['pseudo'].split()[1]
		curseur_balance=conn.execute("select balance from users where name=? and first_name=? " , [nom, prenom])
		userid = conn.execute("select id from users where name=? and first_name=? ", [nom, prenom])
		userid	= userid.fetchone()[0]
		balance = curseur_balance.fetchone()[0]
		if type_cours == 'Multiple':
			with st.form('Orders'):
				total = 0
				st.title("Trading")
				instruments = get_data()
				asset = st.multiselect('Click below to select a new asset', instruments.index.sort_values(), format_func=label)
				order_side=st.selectbox('Side', ['Buy', 'Sell'], key=1)
				today = pd.to_datetime('today')
				last_weekday = prev_weekday(pd.to_datetime('today'))
				quantity = st.number_input('Select the quantity', min_value=1, step=1)
				if len(asset) == 1:
					data0 = load_quotes(''.join(str(asset)[2:-2]), last_weekday, today)
					data = data0.copy().dropna()
					data.index.name = None
					data = data['Adj Close'].iloc[-1]
				elif len(asset) > 1:
					data0 = load_quotes(''.join(str(asset).replace('[','').replace(']','').replace('\'','')), last_weekday, today)
					data = data0.copy().dropna()
					data.index.name = None
					data = data['Adj Close'].iloc[-1]
				st.write('Balance : '+str(balance))
				submit= st.form_submit_button('Send order')
				if submit:
					if len(asset) > 1:
						for elem,instr in zip(data.tolist(), asset):
							st.write('Last close for '+instr+' is : '+str(elem))
							amount = elem*quantity
							st.write('Amount of order : '+str(amount))
							total += amount
							conn.execute("INSERT INTO orders (ticker, order_type,price, quantity,side,date, user_id) VALUES (?,?,?,?,?,?,?)", [instr, type_cours,amount,quantity,order_side,str(today), userid])
							balance=balance-total
							conn.execute("UPDATE users SET  balance=? where id=?", [balance, userid])
							conn.commit()
						st.write('Total :'+str(int(total))+' $')
					else:
						st.write('Last close for '+str(asset)+' is : '+str(data))
						amount = data*quantity
						st.write('Amount of order : '+str(amount)+' $')
						conn.execute("INSERT INTO orders (ticker, order_type,price, quantity,side,date, user_id) VALUES (?,?,?,?,?,?,?)", [asset[0], type_cours,amount,quantity,order_side,str(today), userid])
						balance=balance-amount
						conn.execute("UPDATE users SET  balance=? where id=?", [balance, userid])
						conn.commit()
		elif type_cours == 'Unique':
			with st.form('Orders unique'):
				st.title("Trading")
				instruments = get_data()
				ticker = st.selectbox('Click below to select a new asset',instruments.index.sort_values(),format_func=label)
				order_side=st.selectbox('Side', ['Buy', 'Sell'], key=1)
				quantity = st.number_input('Select the quantity', min_value=1, step=1)
				today = pd.to_datetime('today')
				last_weekday = prev_weekday(pd.to_datetime('today'))
				data0 = load_quotes(ticker, last_weekday, today)
				data = data0.copy().dropna()
			
				data.index.name = None
				data = data['Adj Close'].iloc[-1]
				st.write('Balance : '+str(balance))
				st.write('Last close for this instrument is : '+str(data))
				amount = data*quantity
				balance = balance-amount
				confirm = st.form_submit_button('Confirm order')
				if confirm:
					conn.execute("INSERT INTO orders (ticker, order_type,price, quantity,side,date, user_id) VALUES (?,?,?,?,?,?,?)", [ticker, type_cours,amount,int(quantity),order_side,str(today), userid])
					conn.execute("UPDATE users SET  balance=? where id=?", [balance, userid])
					conn.commit()
					st.write('Amount of order : '+str(data*quantity)+' $')
		display_data_ordre(conn)
	else:
		st.title('Please connect before accessing this page')

PAGES = {
	"Home":home,
	"Login":connect,
	"Trading":orders,
	"My account / Sign up":signup
}

def main():
	st.sidebar.title("Select Page")
	page_selected = st.sidebar.radio("Select", list(PAGES.keys()))
	PAGES[page_selected]()
	conn = get_connection(URI_SQLITE_DB)
	init_db(conn)
	
if __name__ == '__main__':
	main()
