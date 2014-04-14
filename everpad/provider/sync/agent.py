from evernote.edam.error.ttypes import EDAMSystemException
from PySide import QtCore
from datetime import datetime
from ... import const
from ...specific import AppClass
from .. import tools
from . import note, notebook, tag
from .. import models
import time
import traceback
import socket


# ********** SyncThread **********
# 
# from daemon.py 
# subclass PySide.QtCore.QThread and reimplement PySide.QtCore.QThread.run()
# http://srinikom.github.io/pyside-docs/PySide/QtCore/QThread.html
class SyncThread(QtCore.QThread):
    """Sync notes with evernote thread"""
    force_sync_signal = QtCore.Signal()
    sync_state_changed = QtCore.Signal(int)
    data_changed = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        """Init default values"""
        QtCore.QThread.__init__(self, *args, **kwargs)
        
        # non - KDE
        # from PySide.QtCore import QCoreApplication
        # Class = QCoreApplication
        # http://srinikom.github.io/pyside-docs/PySide/QtCore/QCoreApplication.html
        self.app = AppClass.instance()
        # setup timer
        self._init_timer()
        # 
        self._init_locks()


    # *** Initialize Sync
    # ??? initial startup sync
    def _init_sync(self):
        """Init sync"""
        
        # set status         
        self.status = const.STATUS_NONE
        
        # get current datetime
        # https://docs.python.org/2/library/datetime.html#datetime-objects
        # consider time zone?         
        self.last_sync = datetime.now()
        
        # query Sync table
        self.sync_state = self.session.query(models.Sync).first()
        if not self.sync_state:
            self.sync_state = models.Sync(
                update_count=0, last_sync=self.last_sync)
            self.session.add(self.sync_state)
            self.session.commit()

    # *** Initialize Timer
    # Initialize timer, connect to sync signal, set delay,
    # and start timer.
    # http://qt-project.org/doc/qt-4.8/qtimer.html
    def _init_timer(self):
        """Init timer"""
        
        # Constructs a timer
        self.timer = QtCore.QTimer()
        
        # This signal is emitted when the timer times out - sync
        self.timer.timeout.connect(self.sync)
        
        # call update_timer to set time and start
        self.update_timer()

   # *** End Initialize Timer

    def _init_locks(self):
        """Init locks"""
        self.wait_condition = QtCore.QWaitCondition()
        self.mutex = QtCore.QMutex()

    # *** Update Timer
    # Stop the timmer, Set the timer delay to user settings,
    # default value, or nothing if manual. Finally, start the timer.
    def update_timer(self):
        """Update sync timer"""
        
        # stop timer
        self.timer.stop()
        
        # initial value of timer from settings
        delay = int(self.app.settings.value('sync_delay') or 0)
        
        # if no delay has been set in the settings then use
        # the default -  DEFAULT_SYNC_DELAY = 30000 * 60
        # WOW - that is a big default delay
        if not delay:
            delay = const.DEFAULT_SYNC_DELAY

        # if delay is not set to manual - SYNC_MANUAL = -1
        # then start the timer
        if delay != const.SYNC_MANUAL:
            self.timer.start(delay)
            
   # *** End Update Timer

    # ***** reimplement PySide.QtCore.QThread.run() *****   
    def run(self):
        """Run thread"""
        self._init_db()         # setup database
        self._init_network()    # get evernote info
        self._init_sync()       # setup Sync times 
        
        
        # Deprecated since version 2.6: 
        # The mutex module has been removed in Python 3.
        while True:
            self.mutex.lock()
            self.wait_condition.wait(self.mutex)
            
            # do sync ....
            self.perform()
            
            self.mutex.unlock()
            
            # sleep 1 second
            time.sleep(1)  # prevent cpu eating
    # ********** end main running loop **************

    # Setup database - tools.py    
    def _init_db(self):
        """Init database"""
        self.session = tools.get_db_session()

    # Get get_auth_token get_note_store get_user_store - tools.py
    def _init_network(self):
        """Init connection to remote server"""
        while True:
            try:
                self.auth_token = tools.get_auth_token()
                self.note_store = tools.get_note_store(self.auth_token)
                self.user_store = tools.get_user_store(self.auth_token)
                break
            except socket.error:
                time.sleep(30)

    def _need_to_update(self):
        """Check need for update notes"""
        self.app.log('Checking need for update notes.')
        # Try to update_count.
        
        # okay get a RATE_LIMIT_REACHED on an initial sync
        # http://dev.evernote.com/doc/articles/rate_limits.php
        try:
            update_count = self.note_store.getSyncState(
                self.auth_token).updateCount

        except EDAMSystemException, e:
            if e.errorCode == EDAMErrorCode.RATE_LIMIT_REACHED:
                self.app.log("Rate limit reached: %d seconds" % e.rateLimitDuration)
                return False

        except socket.error, e:
            self.app.log(
                "Couldn't connect to remote server. Got: %s" %
                traceback.format_exc())
            # This is most likely a network failure. Return False so
            # everpad-provider won't lock up and can try to sync up in the
            # next run.
            return False
            
        #XXX: matsubara probably innefficient as it does a SQL each time it
        # accesses the update_count attr?
        self.app.log("Local update count: %s Remote update count: %s" % (
            self.sync_state.update_count, update_count))
        reason = update_count != self.sync_state.update_count
        self.sync_state.update_count = update_count
        return reason

    def force_sync(self):
        """Start sync"""
        self.timer.stop()
        self.sync()
        self.update_timer()

    @QtCore.Slot()
    def sync(self):
        """Do sync"""
        self.wait_condition.wakeAll()

    # ******** check for a sync needed *********   
    def perform(self):
        """Perform all sync"""
        self.app.log("Performing sync perform( )")
        self.status = const.STATUS_SYNC
        self.last_sync = datetime.now()
        self.sync_state_changed.emit(const.SYNC_STATE_START)

        need_to_update = self._need_to_update()

        try:
            if need_to_update:
                self.remote_changes()
            self.local_changes()
        except Exception, e:  # maybe log this
            self.session.rollback()
            self._init_db()
            self.app.log(e)
        finally:
            self.sync_state_changed.emit(const.SYNC_STATE_FINISH)
            self.status = const.STATUS_NONE
            self.all_notes = None

        self.data_changed.emit()
        self.app.log("Sync performed.")

    def _get_sync_args(self):
        """Get sync arguments"""
        return self.auth_token, self.session, self.note_store, self.user_store

    # Send all changes to server (evernote) 
    def local_changes(self):
        """Send local changes to evernote server"""
        self.app.log('Running local_changes()')

        # Notebooks
        self.sync_state_changed.emit(const.SYNC_STATE_NOTEBOOKS_LOCAL)
        notebook.PushNotebook(*self._get_sync_args()).push()

        # Tags
        self.sync_state_changed.emit(const.SYNC_STATE_TAGS_LOCAL)
        tag.PushTag(*self._get_sync_args()).push()

        # Notes and Resources
        self.sync_state_changed.emit(const.SYNC_STATE_NOTES_LOCAL)
        note.PushNote(*self._get_sync_args()).push()

    # Get all changes from server (evernote) 
    def remote_changes(self):
        """Receive remote changes from evernote"""
        self.app.log('Running remote_changes()')
        
        # Notebooks
        self.sync_state_changed.emit(const.SYNC_STATE_NOTEBOOKS_REMOTE)
        notebook.PullNotebook(*self._get_sync_args()).pull()
        
        # Tags
        self.sync_state_changed.emit(const.SYNC_STATE_TAGS_REMOTE)
        tag.PullTag(*self._get_sync_args()).pull()

        # Notes and Resources
        self.sync_state_changed.emit(const.SYNC_STATE_NOTES_REMOTE)
        note.PullNote(*self._get_sync_args()).pull()
