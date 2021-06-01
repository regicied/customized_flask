from flask import Blueprint
from backend.myBluePrint.ericic.api.v1.dataCenterView import DataCenter
from backend.myBluePrint.ericic.api.v1.vmView import VmView
from backend.myBluePrint.ericic.api.v1.hostView import HostView
from backend.myBluePrint.ericic.api.v1.recordView import RecordView
from backend.myBluePrint.ericic.api.v1.recordResultView import RecordResultView
from backend.myBluePrint.ericic.api.v1.connStateView import ConnectStatusView
from backend.myBluePrint.ericic.api.v1.uploadView import Upload
from backend.myBluePrint.ericic.api.v1.downloadView import DownloadView
from backend.myBluePrint.ericic.api.v1.cpuLayoutView import CPULayoutView
from backend.myBluePrint.ericic.api.v1.PieChartsView import PieChartsView
from backend.myBluePrint.ericic.api.v1.dataRefreshView import DataRefreshView

ericic_bp = Blueprint('ericic', __name__, url_prefix='/api/ericic/v1/')

ericic_bp.add_url_rule('data_center', view_func=DataCenter.as_view('DataCenter'))
ericic_bp.add_url_rule('vm_info', view_func=VmView.as_view('VmView'))
ericic_bp.add_url_rule('host_info', view_func=HostView.as_view('HostView'))
ericic_bp.add_url_rule('record', view_func=RecordView.as_view('RecordView'))
ericic_bp.add_url_rule('record_result', view_func=RecordResultView.as_view('RecordResultView'))
ericic_bp.add_url_rule('connect_status', view_func=ConnectStatusView.as_view('ConnectStatusView'))
ericic_bp.add_url_rule('data_center/upload', view_func=Upload.as_view('Upload'))
ericic_bp.add_url_rule('download', view_func=DownloadView.as_view('DownloadView'))
ericic_bp.add_url_rule('cpu_layout', view_func=CPULayoutView.as_view('CPULayoutView'))
ericic_bp.add_url_rule('pie_charts', view_func=PieChartsView.as_view('PieChartView'))
ericic_bp.add_url_rule('data_refresh', view_func=DataRefreshView.as_view('DataFreshView'))
