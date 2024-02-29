from simulator import simulator
import wx
if __name__ == '__main__':
    app = wx.App(False)
    frame = simulator.Simulator(None)
    frame.Show(True)
    app.MainLoop()
