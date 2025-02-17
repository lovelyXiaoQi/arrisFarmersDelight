# -*- coding: utf-8 -*-
from SystemApi import *
import time

_TimerData = list()
_ComponentMap = dict()


class _Timer(object):
    def __init__(self, Time, Func, Data, While):
        self.DefaultTime = 0
        self.Time = Time
        self.Func = Func
        self.Data = Data
        self.Stop = False
        self.While = While
        self.Destroy = False
        self.startTime = time.time()


@ListenServer("OnScriptTickServer")
def _ComputeTimerServer():
    for Timer in _TimerData:
        NowTime = time.time()
        if Timer.Stop:
            continue
        if NowTime-Timer.startTime < Timer.Time:
            continue
        Func = Timer.Func
        Data = Timer.Data
        try:
            Func(*Data)
        except Exception as error:
            import traceback
            traceback.print_exc()
            Timer.Destroy = True
            _TimerData.remove(Timer)
            del Timer
            continue
        if Timer.While:
            Timer.startTime = time.time()
            continue
        Timer.Destroy = True
        _TimerData.remove(Timer)
        del Timer


def SetTimerState(Timer, State):
    """
    设置延时器运行状态(是否暂停延时器)

    :param Timer: 延时器对象
    :param State: 开关状态(True为开始延时，False为暂停延时)
    """
    Timer.Stop = State


def DestroyTimer(Timer):
    """
    注销延时器(完全销毁，注销后无法再对该延时器对象进行有效操作)

    :param Timer: 延时器对象
    """
    Timer.Destroy = True
    Timer.Stop = True
    if Timer in _TimerData:
        _TimerData.remove(Timer)
    del Timer


def SetTimerTime(Timer, Time, Keep=False):
    """
    动态修改延时器时间

    :param Timer: 延时器对象
    :param Time: 要设置的时间
    :param Keep: 是否接上之前已经经过的时间，设置为True则会沿已经经过的时间继续计时，否则清空之前的时间，重新计时
    """
    Timer.Time = Time
    if not Keep:
        Timer.startTime = time.time()
    if not Time:
        _ComputeTimerServer()
    Timer.DefaultTime = Timer.Time


def CreateTimer(Time, Func, While, *args):
    """
    创建延时器，用于延时执行函数任务

    :param Time: 延时的时间，单位为秒/s
    :param Func: 延时执行的函数，函数将会在指定时间后执行
    :param While: 是否循环延时执行，启动后延时器会重复间隔指定时间后执行一次函数，可用StopTimer停止或DestroyTimer彻底注销
    :param args: 延时函数执行时所需要的参数
    :return: Timer 该延时器的可操作对象
    """
    Timer = _Timer(Time, Func, args, While)
    Timer.DefaultTime = Timer.Time
    _TimerData.append(Timer)
    return Timer


def GetComponent(ComponentName):
    return _ComponentMap.get(ComponentName, None)


def LoadingComponent(BaseCompClass):
    BaseCompObj = BaseCompClass() #type: BaseComponent
    for obj in BaseCompClass.__dict__.values():
        if hasattr(obj, "__listener__"):
            Event = obj.__event__
            className = BaseCompClass.__name__
            _AddListen(BaseCompObj, Event, obj, className)
        if hasattr(obj, "__caller__"):
            ForAllMod = obj.__for_all_mod__
            _AddCall(BaseCompObj, ForAllMod, obj)

def _AddListen(BaseCompObj, Event, obj, className):
    def Func(*args, **kwargs):
        func = getattr(BaseCompObj, obj.__name__)
        return func(*args, **kwargs)
    Func.__name__ = "%s_%s" % (className, obj.__name__)
    BaseCompObj.UnListenEvent(Event, Func)
    ListenServerEvents(Event, Func)
    BaseCompObj._ListenMap.append([Event, Func])


def _AddCall(BaseCompObj, ForAllMod, obj):
    def Func(*args, **kwargs):
        func = getattr(BaseCompObj, obj.__name__)
        return func(*args, **kwargs)
    Func.__name__ = obj.__name__
    BaseCompObj.UnListenCall(Func)
    CallBack(Func, "-1", ForAllMod)
    BaseCompObj._CallMap.append(Func)


class BaseComponent(object):
    def __init__(self):
        self._ListenMap = list()
        self._CallMap = list()
        if _ComponentMap.get(str(type(self).__name__)):
            LastComponent = _ComponentMap[str(type(self).__name__)] #type: BaseComponent
            LastComponent.DestroyComponent()
            _ComponentMap.pop(str(type(self).__name__))
        _ComponentMap[str(type(self).__name__)] = self
        pass

    def UnListenEvent(self, Event, Func):
        if [Event, Func] not in self._ListenMap:
            return
        self._ListenMap.remove([Event, Func])
        UnListenServer(Event, Func)

    def UnListenCall(self, Func):
        if Func not in self._CallMap:
            return
        self._CallMap.remove(Func)
        UnListenServerCall(Func)

    def DestroyComponent(self):
        print "[销毁组件]%s" % self
        for Data in self._ListenMap:
            Event, Func = Data
            self.UnListenEvent(Event, Func)

    def __del__(self):
        self.DestroyComponent()

    @staticmethod
    def ComponentListenEvent(Event):
        def Func(func):
            func.__listener__ = True
            func.__event__ = Event
            return func
        return Func

    @staticmethod
    def ComponentListenCall(ForAllMod=False):
        def Func(func):
            func.__caller__ = True
            func.__for_all_mod__ = ForAllMod
            return func
        return Func


print "\n%s[QyMod] ServerMod加载完毕" % Bcolors.SUC