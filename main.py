from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock

import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import os
import serial
# from pyfirmata import Arduino, util, Port
import time
from datetime import datetime, timedelta
import struct
from random import randint
from time import sleep

win_ = Window
connected = False

try:
    ser = serial.Serial("/dev/ttyACM0", 9600)
    connected = True
except:
    print 'Serial connection not established!'
    connected = False

class RToxMain(BoxLayout):
    def show_save(self):
        popup_save = Popup(title='...', size_hint=(0.9,0.9), separator_color=(1,0,0,1))

        fbrowser_cont = BoxLayout(size_hint=(1,1), orientation='vertical')
        fc_i = FileChooserIconView(size_hint=(1,0.9))
        text_input = TextInput(size_hint=(1, 0.05), id='fname', multiline=False)
        btn_cont = BoxLayout(orientation='horizontal', size_hint=(1,0.05))
        ok_btn = Button(text='OK', size_hint=(0.5,1))
        cls_btn = Button(text='Cancel', size_hint=(0.5,1))

        btn_cont.add_widget(ok_btn)
        btn_cont.add_widget(cls_btn)

        fbrowser_cont.add_widget(text_input)
        fbrowser_cont.add_widget(fc_i)
        fbrowser_cont.add_widget(btn_cont)
        popup_save.add_widget(fbrowser_cont)

        cls_btn.bind(on_press=popup_save.dismiss)
        ok_btn.bind(on_press=lambda a: self.getpath(fc_i.path+'/'+text_input.text))
        ok_btn.bind(on_release=popup_save.dismiss)

        popup_save.open()

    def getpath(self, path):
        global start
        start = False
        global filepath
        global logpath
        filepath = path
        filename, file_extension = os.path.splitext(filepath)
        logpath = filename + '.rtox'
        if file_extension != '.csv':
            filepath += '.csv'
        else:
            pass
        self.ids.path_.text = filepath

    def leave_prog(self):
        App.get_running_app().stop()

    def clear_all(self):
        self.ids.path_.text = ''
        self.ids.dur_meas.text = ''
        self.ids.rec_freq.text = ''
        self.ids.dur_pump.text = ''
        self.ids.pump_freq.text = ''

    def start_meas(self):
        try:
            global start
            start = not start
            if start == True:
                global t_meas
                global f_meas
                global t_pump
                global f_pump

                global out_file_user
                global out_file_log

                global data_log #callback event
                global pump_control #callback event
                global label_upd #callback event
                global time_label_upd

                global start_time
                global stop_time

                global remain_meas
                global remain_pump

                global pump_on

                global plot_data_1
                global plot_data_2
                global plot_data_3
                global plot_data_4
                global plot_data_5
                global plot_data_6
                global plot_data_7
                global plot_data_8
                global plot_data_9
                global plot_data_10
                global plot_time

                plot_data_1 = []
                plot_data_2 = []
                plot_data_3 = []
                plot_data_4 = []
                plot_data_5 = []
                plot_data_6 = []
                plot_data_7 = []
                plot_data_8 = []
                plot_data_9 = []
                plot_data_10 = []
                plot_time = []

                t_meas = int(self.ids.dur_meas.text)*60
                f_meas = int(self.ids.rec_freq.text)
                t_pump = int(self.ids.dur_pump.text)
                f_pump = int(self.ids.pump_freq.text)*60

                print 'Path to file: ', filepath
                print 'Duration of measurement: ', t_meas
                print 'Frequency of recording: ', f_meas
                print 'Duration of pumping: ', t_pump
                print 'Frequency of pumping: ', f_pump

                out_file_user = open(filepath, 'w')
                out_file_log = open(logpath, 'w')

                out_file_user.write('date-time;exp_1;exp_2;exp_3;exp_4;exp_5;exp_6;exp_7;exp_8;light;temp')
                out_file_log.write('date-time;ref_R;ref_C;noise;d_ref;exp_1_R;exp_1_C;d_exp_1;exp_2_R;exp_2_C;d_exp_2;exp_3_R;exp_3_C;d_exp_3;exp_4_R;exp_4_C;d_exp_4;exp_5_R;exp_5_C;d_exp_5;exp_6_R;exp_6_C;d_exp_6;exp_7_R;exp_7_C;d_exp_7;exp_8_R;exp_8_C;d_exp_8;light;temp')

                self.ids.start_btn.text = 'Stop and save'
                self.ids.clear_btn.disabled = True
                self.ids.browse_btn.disabled = True
                self.ids.dur_meas.disabled = True
                self.ids.rec_freq.disabled = True
                self.ids.dur_pump.disabled = True
                self.ids.pump_freq.disabled = True

                start_time = datetime.now()
                stop_time = start_time + timedelta(seconds=t_meas)

                pump_on = start_time + timedelta(seconds=f_pump)

                data_log = Clock.schedule_interval(self.callback_data, f_meas)
                pump_control = Clock.schedule_interval(self.callback_act_pump, f_pump)
                label_upd = Clock.schedule_interval(self.callback_label_upd, 10)
                time_label_upd = Clock.schedule_interval(self.callback_time_label_upd, 1)
                #param_det = Clock.schedule_once(self.callback_param_det, 8)

            elif start == False:
                self.end_meas()

        except (ValueError, NameError):
            popup_ = Popup(title='Warning', size_hint=(0.3,0.2), separator_color=(1,0,0,1))
            box_1 = BoxLayout(orientation = 'vertical')
            lab = Label(text='Insufficient data!')
            ok_btn = Button(text='OK')
            box_1.add_widget(lab)
            box_1.add_widget(ok_btn)
            popup_.add_widget(box_1)

            ok_btn.bind(on_release=popup_.dismiss)

            popup_.open()

    def callback_param_det(self, dt):
        global c0_av
        global d_exp1
        global d_exp2
        global d_exp3
        global d_exp4
        global d_exp5
        global d_exp6
        global d_exp7
        global d_exp8

        co2 = (ser.readline()).strip()
        splitted = co2.split(";")

        c0_av = (int(splitted[0]) + int(splitted[2]) + int(splitted[3]) + int(splitted[4]) + int(splitted[5]) + int(splitted[6]) + int(splitted[7]) + int(splitted[8]) + int(splitted[9]))/9

        d_exp1 = int(splitted[2])-c0_av
        d_exp2 = int(splitted[3])-c0_av
        d_exp3 = int(splitted[4])-c0_av
        d_exp4 = int(splitted[5])-c0_av
        d_exp5 = int(splitted[6])-c0_av
        d_exp6 = int(splitted[7])-c0_av
        d_exp7 = int(splitted[8])-c0_av
        d_exp8 = int(splitted[9])-c0_av

    def draw(self):
        try:
            plt.clf()
        except:
            pass
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('time')
        ax1.plot(plot_data_1, label='Exp1')
        ax1.plot(plot_data_2, label='Exp2')
        ax1.plot(plot_data_3, label='Exp3')
        ax1.plot(plot_data_4, label='Exp4')
        ax1.plot(plot_data_5, label='Exp5')
        ax1.plot(plot_data_6, label='Exp6')
        ax1.plot(plot_data_7, label='Exp7')
        ax1.plot(plot_data_8, label='Exp8')
        ax1.set_ylabel('c(CO2) / [ppm]')
        plt.legend(bbox_to_anchor=(1.15,1), loc="upper left", borderaxespad=0)

        ax2 = ax1.twinx()
        ax2.plot(plot_data_9, label='light')
        ax2.plot(plot_data_10, label='temperature')
        ax2.set_ylabel('light ; temperature / [C]')
        fig.tight_layout()
        fig.subplots_adjust(right=0.70)
        plt.legend(bbox_to_anchor=(1.15,0), loc="lower left", borderaxespad=0)

        print plot_data_9
        print plot_data_10

        popup_plt = Popup(title='Graphical representation of data', size_hint=(0.9,0.9), separator_color=(1,0,0,1))
        plt_box = BoxLayout(size_hint_y=0.95)
        plt_box.add_widget(FigureCanvasKivyAgg(plt.gcf()))
        box_btn = BoxLayout(orientation='horizontal', size_hint_y=0.05)
        cls_btn = Button(text='Close')
        box_btn.add_widget(cls_btn)
        cont_box=BoxLayout(orientation='vertical')
        cont_box.add_widget(plt_box)
        cont_box.add_widget(box_btn)
        popup_plt.add_widget(cont_box)

        popup_plt.open()

        cls_btn.bind(on_release=popup_plt.dismiss)

    def callback_time_label_upd(self, dt):
        now = datetime.now()
        rem_m = (stop_time - now).total_seconds()
        if rem_m <= 0:
            rem_m = 0
        rem_p = (pump_on - now).total_seconds()
        self.ids.meas_rem.text = ('{}:{}:{}'.format(str(int(rem_m // 3600)).zfill(2), str(int(rem_m % 3600 // 60)).zfill(2), str(int(rem_m % 60)).zfill(2)))
        self.ids.pump_rem.text = ('{}:{}:{}'.format(str(int(rem_p // 3600)).zfill(2), str(int(rem_p % 3600 // 60)).zfill(2), str(int(rem_p % 60)).zfill(2)))

        if rem_m <= 0:
            self.end_meas()


    def callback_label_upd(self, dt):
        global co2
        global s1
        global s2
        global s3
        global s4
        global s5
        global s6
        global s7
        global s8
        global temp
        global phot
        #ser.flushInput()
        #ser.flushOutput()
        ser.write(struct.pack('>B',2))
        sleep(0.1)
        co2 = (ser.readline()).strip()
        # print co2
        splitted = co2.split(";")
        s1 = int(splitted[5])
        s2 = int(splitted[8])
        s3 = int(splitted[11])
        s4 = int(splitted[14])
        s5 = int(splitted[17])
        s6 = int(splitted[20])
        s7 = int(splitted[23])
        s8 = int(splitted[26])
        phot = float(splitted[28])
        temp = float(splitted[29])
        
        #try:
        self.ids.exp_1.text = str(s1)
        self.ids.exp_2.text = str(s2)
        self.ids.exp_3.text = str(s3)
        self.ids.exp_4.text = str(s4)
        self.ids.exp_5.text = str(s5)
        self.ids.exp_6.text = str(s6)
        self.ids.exp_7.text = str(s7)
        self.ids.exp_8.text = str(s8)

        self.ids.temp.text = str(temp)

        #except:
        #    print 'Greska!'

    def callback_data(self, dt):
        #ser.flushInput() #treba li?
        #ser.flushOutput()

        #global co2
        global plot_data_1
        global plot_data_2
        global plot_data_3
        global plot_data_4
        global plot_data_5
        global plot_data_6
        global plot_data_7
        global plot_data_8
        global plot_data_9
        global plot_data_10
        global plot_time

        print 'Writing into file'
        now_str = str(datetime.now().strftime("%Y%m%d-%H:%M:%S"))
        now = datetime.now()
        print now
        #co2 = (ser.readline()).strip()
        # print co2
        out_file_log.write("\n"+now_str+";"+co2)
        #splitted = co2.split(";")
        user_data = 'data-missing'
        try:
            user_data = "\n{};{};{};{};{};{};{};{};{};{};{}".format(now_str, s1, s2, s3, s4, s5, s6, s7, s8, phot, temp)
            plot_data_1.append(s1)
            plot_data_2.append(s2)
            plot_data_3.append(s3)
            plot_data_4.append(s4)
            plot_data_5.append(s5)
            plot_data_6.append(s6)
            plot_data_7.append(s7)
            plot_data_8.append(s8)
            plot_data_9.append(phot)
            plot_data_10.append(temp)
            plot_time.append(now_str)
        except:
            pass
        print user_data
        out_file_user.write(user_data)
        out_file_log.flush()
        out_file_user.flush()

    def callback_act_pump(self, dt):
        print 'Activating pump'
        global pump_on
        pump_on = datetime.now()+timedelta(seconds=f_pump)
        self.ids.pump_img.source = 'pump_active.gif'
        try:
            ser.write(struct.pack('>B',1))
        except:
            pass
        Clock.schedule_once(self.callback_inact_pump, t_pump)

    def callback_inact_pump(self, dt):
        print 'Inactivating pump'
        self.ids.pump_img.source = 'pump_inactive.png'
        try:
            ser.write(struct.pack('>B',0))
        except:
            pass

    def end_meas(self):
        global label_upd
        global pump_control
        global data_log
        global time_label_upd

        time_label_upd.cancel()
        out_file_user.close()
        out_file_log.close()

        data_log.cancel()
        pump_control.cancel()
        label_upd.cancel()

        self.ids.start_btn.text = 'Start'
        self.ids.clear_btn.disabled = False
        self.ids.browse_btn.disabled = False
        self.ids.dur_meas.disabled = False
        self.ids.rec_freq.disabled = False
        self.ids.dur_pump.disabled = False
        self.ids.pump_freq.disabled = False
        self.ids.pump_img.source = 'pump_inactive.png'
        self.ids.meas_rem.text = ''
        self.ids.pump_rem.text = ''

        self.ids.exp_1.text = ''
        self.ids.exp_2.text = ''
        self.ids.exp_3.text = ''
        self.ids.exp_4.text = ''
        self.ids.exp_5.text = ''
        self.ids.exp_6.text = ''
        self.ids.exp_7.text = ''
        self.ids.exp_8.text = ''

        self.ids.temp.text = ''

# class SerialWarning(BoxLayout):
#     pass

class RToxApp(App):
    def build(self):
        return RToxMain()

    def on_start(self):
        if connected == False:
            popup_ = Popup(title='Warning', size_hint=(0.5,0.3), separator_color=(1,0,0,1))
            box_1 = BoxLayout(orientation = 'vertical')
            lab = Label(text='Serial connection not established!')
            ok_btn = Button(text='OK', size_hint_y = 0.35)
            box_1.add_widget(lab)
            box_1.add_widget(ok_btn)
            popup_.add_widget(box_1)

            # ok_btn.bind(on_release=lambda a:self.stop_app())

            popup_.open()

    def stop_app(self):
        App.get_running_app().stop()

if __name__=='__main__':
    RToxApp().run()
