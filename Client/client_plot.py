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
		self.exit_btn = QPushButton("Exit")
		#self.show_btn.resize(200,400)
		self.show_btn.clicked.connect(self.show_graph)
		self.exit_btn.clicked.connect(self.exit_ui)

		
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
		rightLayout.addWidget(self.exit_btn)
		rightLayout.addWidget(self.cal)
		rightLayout.addStretch(1)

		layout = QHBoxLayout()
		layout.addLayout(leftLayout)
		layout.addLayout(rightLayout)
		layout.setStretchFactor(leftLayout, 4)
		layout.setStretchFactor(rightLayout, 1)

		self.setLayout(layout)


	def show_graph(self):
		search_date = self.cal.selectedDate().toString('yyyy-MM-dd')
		send_data = {'type': 'request', 'data':{'name': self.hostname,
		'session': self.user_session,
		'date': search_date
		}}
		resp = cp.main(send_data)
		self.draw_graph(resp['data']['detail'])

	def draw_graph(self, resp):
		#10분 간격 graph
		self.axis_cpu.cla()
		self.axis_net.cla()
		self.axis_bd.cla()
		self.set_graph_label()#지웠다가 다시 그림

		share_x = range(0, 1440, 10)
		cpu_y = [float(m) for m in resp['cpu']]#to float
		net_y = resp['network']#0 1
		bd_y = resp['bd']#0 1
		tx_y = [int(t[0]) for t in net_y]
		rx_y = [int(r[1]) for r in net_y]

		rd_y = [int(m[0]) for m in bd_y]
		wr_y = [int(m[1]) for m in bd_y]#int형으로 전환

		net_lim = max(tx_y) if max(tx_y) !=0 else 1
		bd_lim = max(rd_y) if max(rd_y) !=0 else 1
		self.axis_cpu.set_ylim([0, 100])
		self.axis_net.set_ylim([0, net_lim])
		self.axis_bd.set_ylim([0, bd_lim])

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

	def exit_ui(self):
		self.axis_cpu.cla()
		self.show_btn.clicked.disconnect()
		self.exit_btn.clicked.disconnect()
		self.close()
		

if __name__ == '__main__':
	app = QApplication([])
	window = PlotWindow('a','b')
	window.show()
	app.exec()
