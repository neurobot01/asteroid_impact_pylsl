import xml.etree.ElementTree as ET
import json
import time
from dataclasses import dataclass
from contextlib import contextmanager

import pylsl
import requests
from rich import print_json
from pydantic import BaseModel

try:
    from api.models import *
except ImportError:
    from models import *

class AuroraRequestError(Exception):
    pass

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def is_ip_reachable(ip: str, port: int) -> bool:
    try:
        return requests.get(f"http://{ip}:{port}/api/v1/ping", timeout=1).status_code == 200
    except:
        return False

def launch_aurora(ip: str, port: int) -> int:
    resp = do_request(f"http://{ip}:{port}/api/v1/aurora/start", method="POST")
    return resp["port"]


def do_request(url, method="GET", data={}, auth=None, debug=False, timeout=20):
    headers = {"Content-Type": "application/json"}

    if isinstance(data, dict):
        data = json.dumps(data)
    elif isinstance(data, BaseModel):
        data = data.json()

    if debug:
        print("Sending request:")
        print(f"  Request: {method} {url}")
        print(f"  Data: {data}")
        print(f"  Headers: {headers}")
        print(f"  Auth: {auth}")
    try:
        if method == "GET":
            response = requests.get(url, auth=auth, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, data=data, headers=headers, auth=auth, timeout=timeout)
        else:
            raise ValueError(f"Invalid method: {method}")
        response.raise_for_status()
        if debug:
            print("Response:", response.status_code)
            print_json(data=response.json())
        return response.json()
    except requests.exceptions.HTTPError as err:
        print("ERROR: ", err.response.status_code, err.response.reason)
        print("Explanation: ", err.response.json())
        raise AuroraRequestError(err.response.json())
    except requests.exceptions.Timeout:
        raise SystemExit("Timeout when connecting to Aurora")
    except:
        raise SystemExit("Error when connecting to Aurora")


@dataclass
class AuroraInstanceInfo:
    ip: str
    port: int
    host: str


@contextmanager
def aurora_connection(connection_info: AuroraInstanceInfo, debug_requests=False):
    aurora = Aurora(connection_info, debug_requests)
    aurora.connect()
    try:
        yield aurora
    finally:
        aurora.disconnect()


class Aurora:
    def __init__(self, connection_info: AuroraInstanceInfo, debug_requests=False):
        self.base_url = f"http://{connection_info.ip}:{connection_info.port}/api/v1"
        self.hostname = connection_info.host
        self.bearer = None
        self.debug_requests = debug_requests

    @staticmethod
    def start_instance() -> AuroraInstanceInfo:
        streams = pylsl.resolve_byprop("name", "Aurora API launcher", timeout=4)
        if len(streams) == 0:
            raise ValueError("Could not find Aurora launcher")
        if len(streams) > 1:
            raise ValueError("Found multiple Aurora launchers")
        inlet = pylsl.stream_inlet(streams[0])
        inlet.open_stream()
        info = ET.fromstring(inlet.info().as_xml())
        host = info.find("hostname").text
        launcher_port = int(info.find("desc").find("port").text)
        for ip in info.find("desc").findall("v4address"):
            print(f"Trying {ip.text}:{launcher_port}")
            if is_ip_reachable(ip.text, launcher_port):
                print(f"Found Aurora launcher at {ip.text}:{launcher_port} on host {host}")
                aurora_port = launch_aurora(ip.text, launcher_port)
                print(f"Launching Aurora at {ip.text}:{aurora_port} on host {host}")
                start = time.time()
                while not is_ip_reachable(ip.text, aurora_port) and time.time() - start < 15:
                    print(f"Waiting for Aurora to start...")
                    time.sleep(1)
                if is_ip_reachable(ip.text, aurora_port):
                    print(f"Aurora started successfully!")
                else:
                    raise ValueError("Could not connect to Aurora instance")
                return AuroraInstanceInfo(ip.text, aurora_port, host)
        raise ValueError("Could not find Aurora launcher")

    @staticmethod
    def discover_instances() -> list[AuroraInstanceInfo]:
        streams = pylsl.resolve_byprop("name", "Aurora_API", minimum=10, timeout=4)
        instances: list[AuroraInstanceInfo] = []
        for stream_info in streams:
            try:
                inlet = pylsl.stream_inlet(stream_info)
                inlet.open_stream()
                info = ET.fromstring(inlet.info().as_xml())
            except pylsl.LostError:
                print("Lost error")
                continue
            finally:
                if inlet is not None:
                    inlet.close_stream()

            host = info.find("hostname").text
            port = int(info.find("desc").find("port").text)
            for ip in info.find("desc").findall("v4address"):
                print(f"Trying {ip.text}:{port}")
                if is_ip_reachable(ip.text, port):
                    print(f"Found Aurora at {ip.text}:{port} on host {host}")
                    instances.append(AuroraInstanceInfo(ip.text, port, host))
        return instances

    def connect(self):
        res = do_request(self.base_url + "/connect", debug=self.debug_requests)
        self.bearer = BearerAuth(res["api_token"])

    def disconnect(self):
        return do_request(self.base_url + "/disconnect", auth=self.bearer, method="POST", debug=self.debug_requests)

    def info(self):
        res = do_request(self.base_url + "/aurora/info", debug=self.debug_requests)
        return AuroraInfo(**res)

    def settings(self, aurora_settings=None):
        if aurora_settings is not None:
            res = do_request(self.base_url + "/aurora/settings",
                             method="POST",
                             data=aurora_settings,
                             auth=self.bearer,
                             debug=self.debug_requests)
            return res
        else:
            res = do_request(self.base_url + "/aurora/settings", auth=self.bearer, debug=self.debug_requests)
            return AuroraSettings(**res)

    def reset_settings(self):
        res = do_request(self.base_url + "/aurora/settings/reset",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def minimize_window(self):
        res = do_request(self.base_url + "/aurora/window/minimize",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def restore_window(self):
        res = do_request(self.base_url + "/aurora/window/restore",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def alert_window(self):
        res = do_request(self.base_url + "/aurora/window/alert",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def list_devices(self):
        res = do_request(self.base_url + "/devices/list", auth=self.bearer, debug=self.debug_requests)
        return NSP2DeviceList(res)

    def select_device(self, device_name: str):
        res = do_request(self.base_url + "/devices/select",
                         method="POST",
                         data={'device_name': device_name},
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def device_status(self):
        res = do_request(self.base_url + "/devices/status", auth=self.bearer, debug=self.debug_requests)
        return NSP2DeviceStatus(**res)

    # def deselect_device(self):
    #     res = do_request(self.base_url + "/devices/deselect", auth=self.bearer, debug=self.debug_requests)
    #     print_json(data=res)

    def list_configurations(self):
        res = do_request(self.base_url + "/configurations/list", auth=self.bearer, debug=self.debug_requests)
        return NSP2ConfigurationList(res)

    def configuration_info(self, config_name: str):
        res = do_request(self.base_url + "/configurations/info",
                         method="POST",
                         data={'configuration_name': config_name},
                         auth=self.bearer,
                         debug=self.debug_requests)
        return NSP2ConfigurationInfo(**res)

    def select_configuration(self, config_name: str):
        res = do_request(self.base_url + "/configurations/select",
                         method="POST",
                         data={'configuration_name': config_name},
                         auth=self.bearer,
                         debug=self.debug_requests,
                         timeout=90)
        return res

    def start_signal_optimization(self):
        res = do_request(self.base_url + "/signal_optimization/start",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def abort_signal_optimization(self):
        res = do_request(self.base_url + "/signal_optimization/abort",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def signal_optimization_status(self):
        res = do_request(self.base_url + "/signal_optimization/status", auth=self.bearer, debug=self.debug_requests)
        return AuroraSignalOptimizationStatus(**res)

    def signal_optimization_result(self):
        res = do_request(self.base_url + "/signal_optimization/result", auth=self.bearer, debug=self.debug_requests)
        return NSP2SignalOptmizationResults(**res)

    def start_continuous_refresh(self):
        res = do_request(self.base_url + "/signal_optimization/start_continuous_refresh",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def stop_continuous_refresh(self):
        res = do_request(self.base_url + "/signal_optimization/stop_continuous_refresh",
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def set_subject_information(self, name: str, gender: str, age: int, contact_info: str = None):
        subject_info = SubjectInformation(name=name, age=age, gender=gender, contact_info=contact_info)
        res = do_request(self.base_url + "/recording/subject_info",
                         method="POST",
                         data=subject_info,
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def set_experiment_information(self, name: str, remarks: str = None):
        experiment_info = ExperimentInformation(name=name, remarks=remarks)
        res = do_request(self.base_url + "/recording/experiment_info",
                         method="POST",
                         data=experiment_info,
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def start_recording(self, preview_mode: bool = False):
        res = do_request(self.base_url + "/recording/start",
                         method="POST",
                         data={'preview_mode': preview_mode},
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res

    def stop_recording(self):
        res = do_request(self.base_url + "/recording/stop", method="POST", auth=self.bearer, debug=self.debug_requests)
        return res

    def recording_status(self):
        res = do_request(self.base_url + "/recording/status", auth=self.bearer, debug=self.debug_requests)
        return AuroraRecordingStatus(**res)

    def trigger(self, trigger_id: int):
        trigger_ = AuroraTrigger(trigger_id=trigger_id)
        res = do_request(self.base_url + "/recording/trigger",
                         data=trigger_,
                         method="POST",
                         auth=self.bearer,
                         debug=self.debug_requests)
        return res
