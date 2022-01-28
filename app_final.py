import pandas as pd
import streamlit as st
import yfinance as yf



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
	st.subheader('Chart')

	def label(symbol):
		mnemonic = instruments.loc[symbol]
		return symbol + ' - ' + mnemonic.Security

	if st.sidebar.checkbox('View companies list'):
		st.dataframe(instruments[['Security',
		'GICS Sector',
		'Date first added',
		'Founded']])
	st.sidebar.subheader('Select asset')
#	asset = st.sidebar.selectbox('Click below to select a new asset',
	#instruments.index.sort_values(), index=3,
	#format_func=label)
	asset = st.sidebar.multiselect('Click below to select a new asset',
	instruments.index.sort_values(), format_func=label)
	start = st.date_input('Start', value = pd.to_datetime('2020-01-01'))
	end = st.date_input('End', value = pd.to_datetime('today'))
	title.title(instruments.loc[asset].Security)
	if st.sidebar.checkbox('View company info', False):
		st.table(instruments[['Security','GICS Sector','Date first added',
		'Founded']].loc[asset])
	if len(asset) > 0:
		data0 = load_quotes(''.join(str(asset)), start, end)
		data = data0.copy().dropna()
		data.index.name = None
	#	section = st.sidebar.slider('Number of quotes', min_value=30,
	#	max_value=min([2000, data.shape[0]]),
	#	value=500,  step=10)
		data2 = data['Adj Close'].to_frame('Adj Close')
		st.line_chart(data2)
	if st.sidebar.checkbox('View statistics'):
		st.subheader('Statistics')
		st.table(data2.describe())

	if st.sidebar.checkbox('View previous closes'):
		st.subheader(f'{asset} historical data')
		st.write(data2)

def connect():
	st.sidebar.title('ok')

PAGES = {
	"Home":home,
	"Connect":connect
}

def main():
	st.sidebar.title("Select Page")
	page_selected = st.sidebar.radio("Select", list(PAGES.keys()))
	PAGES[page_selected]()
	
if __name__ == '__main__':
	main()