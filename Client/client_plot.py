from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import client_protocol as cp

class PlotWindow(QWidget):
	def __init__(self, hostname, session):
		super().__init__()
		self.hostname = hostname
		self.user_session = session
		self.setupUI()

	def setupUI(self):
		self.setGeometry(500, 200, 1200, 800)
		self.setWindowTitle("Graph Demo")

		self.lineEdit = QLineEdit()
		self.show_btn = QPushButton("Show Graph")
		self.del_btn = QPushButton("Show Graasdfph")
		#self.show_btn.resize(200,400)
		self.show_btn.clicked.connect(self.show_graph)
		self.del_btn.clicked.connect(self.test)

		
		self.fig = plt.Figure()
		self.fig.subplots_adjust(hspace=0.5)#상하간격
		self.canvas = FigureCanvas(self.fig)

		self.axis_cpu = self.fig.add_subplot(3,1,1)
		self.axis_net = self.fig.add_subplot(3,1,2)
		self.axis_bd = self.fig.add_subplot(3,1,3)
		self.set_graph_label()
		self.cal =QCalendarWidget()

		leftLayout = QVBoxLayout()
		leftLayout.addWidget(self.canvas)

		rightLayout = QVBoxLayout()
		rightLayout.setSpacing(50)
		rightLayout.addWidget(self.show_btn)
		rightLayout.addWidget(self.del_btn)
		rightLayout.addWidget(self.cal)
		rightLayout.addStretch(1)

		layout = QHBoxLayout()
		layout.addLayout(leftLayout)
		layout.addLayout(rightLayout)
		layout.setStretchFactor(leftLayout, 4)
		layout.setStretchFactor(rightLayout, 1)

		self.setLayout(layout)


	def show_graph(self):
		#print("clicked")
		#print(self.cal.selectedDate().toString('yyyy-MM-dd'))
		search_date = self.cal.selectedDate().toString('yyyy-MM-dd')
		send_data = {'type': 'request', 'data'{'name': self.hostname,
		'session': self.user_session,
		'date': search_date
		}}
		resp = cp.main(send_data)
		self.draw_graph(resp['date']['detail'])

	def draw_graph(self, resp):
		#{cpu: [], net: [], bd:[]} -> x축 : 24시간 5분간격? --> 288개의 점: 0, 5, 10, 15, ...1440
		self.axis_cpu.cla()
		self.set_graph_label()#지웠다가 다시 그림

		share_x = range(0, 1440, 5)
		cpu_y = resp['cpu']
		net_y = resp['network']#0 1
		bd_y = resp['bd']#0 1
		tx_y = [t[0] for t in net_y]
		rx_y = [r[1] for r in net_y]

		rd_y = [m[0] for m in bd_y]
		wr_y = [m[1] for m in bd_y]

		self.axis_cpu.plot(share_x, cpu_y, color='black', linestyle='solid')
		self.axis_net.plot(share_x, tx_y, color='skyblue', linestyle='solid')
		self.axis_net.plot(share_x, rx_y, color='red', linestyle='solid')
		self.axis_bd.plot(share_x, rd_y, color='skyblue', linestyle='solid')
		self.axis_bd.plot(share_x, wr_y, color='red', linestyle='solid')
		self.canvas.draw()

	def set_graph_label(self):
		self.axis_cpu.set_xticks([0, 1440])
		self.axis_cpu.set_xticklabels(['00:00', '24:00'])
		self.axis_net.set_xticks([0, 1440])
		self.axis_net.set_xticklabels(['00:00', '24:00'])
		self.axis_bd.set_xticks([0, 1440])
		self.axis_bd.set_xticklabels(['00:00', '24:00'])

		self.axis_cpu.set_ylabel("CPU(%)")
		self.axis_cpu.set_yticks([0.0, 20.0, 40.0, 60.0, 80.0, 100.0])
		self.axis_net.set_ylabel("Network(tx, rx)")
		self.axis_bd.set_ylabel("Block Device(rd, wr)")

	def test(self):
		self.axis_cpu.cla()
		self.canvas.draw()

if __name__ == '__main__':
	app = QApplication([])
	window = PlotWindow()
	window.show()
	app.exec()
