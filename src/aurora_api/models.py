from typing import Optional
from enum import Enum

from pydantic import BaseModel, RootModel, Field


class DetectorType(str, Enum):
    SINGLE_TIP = 'single_tip'
    DUAL_TIP = 'dual_tip'
    APD = 'apd'


class SignalQuality(str, Enum):
    SATURATED = 'saturated'
    CRITICAL = 'critical'
    ACCEPTABLE = 'acceptable'
    EXCELLENT = 'excellent'


class WingsConnectionStatus(str, Enum):
    DISCONNECTED = 'disconnected'
    SEARCHING = 'searching'
    CONNECTED = 'connected'


class AuroraInfo(BaseModel):
    version: str


class AuroraSettings(BaseModel):
    output_root: Optional[str] = None
    configuration_directory: Optional[str] = None
    confirm_closing: Optional[bool] = None
    enable_preview_mode: Optional[bool] = None
    power_on_usb_device: Optional[bool] = None
    stop_signal_optimization_on_dark_noise: Optional[bool] = None
    block_average_channel_limit: Optional[int] = None
    detector_type: Optional[DetectorType] = None


class AuroraStartMeasurementResult(BaseModel):
    device_state: str
    output_directory: Optional[str] = None


class AuroraStopMeasurementResult(BaseModel):
    device_state: str


class AuroraRecordingStatus(BaseModel):
    '''
    Status of the current recording
    '''
    duration: float
    number_frames: int
    last_trigger_id: Optional[int] = None
    number_triggers: int
    preview_mode: bool
    waiting_for_data: bool


class AuroraSignalOptimizationStatus(BaseModel):
    signal_optimization_status: str
    progress: Optional[float] = None


class NSP2SignalOptimizationChannelResults(BaseModel):
    signal_quality: list[SignalQuality]
    coefficient_of_variation: list[tuple[float, float, SignalQuality]]
    predicted_signal_level: list[tuple[float, float]]


class NSP2SourceBrightness(BaseModel):
    illuminated_sources: list[list[int]]
    brightness_levels: list[list[list[float]]]


class NSP2SignalOptmizationResults(BaseModel):
    detector_dark_noise: list[tuple[tuple[float, SignalQuality], tuple[float, SignalQuality]]]
    source_brightness: NSP2SourceBrightness
    channel_results: NSP2SignalOptimizationChannelResults


class NSP2Configuration(BaseModel):
    name: str


class NSP2ConfigurationList(RootModel):
    root: list[NSP2Configuration]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

class NSP2TriggerColorPair(BaseModel):
    trigger_id: int
    color_oxy: tuple[int, int, int]
    color_deoxy: tuple[int, int, int]

class NSP2ConfigurationInfo(BaseModel):
    name: str
    number_devices: int
    number_sources: int
    number_detectors: int
    number_channels: int
    channels: list[tuple[int, int]]  # List of (source, detector) indices that form channels
    channel_names: list[str]
    sampling_rate: float
    trigger_in_stream_name: str
    data_out_stream_name: str
    trigger_colors: Optional[list[NSP2TriggerColorPair]] = None
    uses_accelerometer: bool
    uses_biosignals: bool


class AuroraTrigger(BaseModel):
    trigger_id: int = Field(..., description="Id of the trigger", examples=[12], ge=1, le=255)


class WingsDevice(BaseModel):
    serial_number: str


class NSP2SecondaryDevice(BaseModel):
    name: str
    serial_number: str


class NSP2Device(BaseModel):
    name: str
    serial_number: str
    connection_type: str
    wings_device: Optional[WingsDevice] = None
    secondary_devices: Optional[list[NSP2SecondaryDevice]] = None


class NSP2DeviceList(RootModel):
    root: list[NSP2Device]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class WingsDeviceStatus(BaseModel):
    serial_number: str
    battery_level: float
    connection_status: WingsConnectionStatus


class NSP2FanSpeeds(BaseModel):
    fan1_speed: int = Field(..., description="Speed level of fan 1", examples=[1], ge=0, le=4)
    fan2_speed: int = Field(..., description="Speed level of fan 2", examples=[3], ge=0, le=4)


class NSP2Temperatures(BaseModel):
    adc_temperature_0: float = Field(..., description="Temperature in Celsius", examples=[28.5])
    adc_temperature_1: float = Field(..., description="Temperature in Celsius", examples=[29.2])
    adc_temperature_2: float = Field(..., description="Temperature in Celsius", examples=[38.1])
    battery_temperature: float = Field(..., description="Battery temperature in Celsius", examples=[34.5])


class NSP2SecondaryDeviceStatus(BaseModel):
    serial_number: str
    temperatures: NSP2Temperatures
    battery_level: float
    fan_speeds: NSP2FanSpeeds
    charging: bool


class NSP2DeviceStatus(BaseModel):
    serial_number: str
    device_state: str
    battery_level: float
    temperatures: NSP2Temperatures
    fan_speeds: NSP2FanSpeeds
    charging: bool
    wings_device_status: Optional[WingsDeviceStatus] = None
    secondary_devices: Optional[list[NSP2SecondaryDeviceStatus]] = None


class SubjectInformation(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact_info: Optional[str] = None


class ExperimentInformation(BaseModel):
    name: Optional[str] = None
    remarks: Optional[str] = None


if __name__ == "__main__":
    import json
    from pydantic.type_adapter import TypeAdapter
    _, top_level_schema = TypeAdapter.json_schemas(
        [(AuroraInfo, 'validation', TypeAdapter(AuroraInfo)),
         (AuroraStartMeasurementResult, 'validation', TypeAdapter(AuroraStartMeasurementResult)),
         (AuroraStopMeasurementResult, 'validation', TypeAdapter(AuroraStopMeasurementResult))],
        ref_template='#/components/schemas/{model}')
    print(json.dumps(top_level_schema, indent=2))