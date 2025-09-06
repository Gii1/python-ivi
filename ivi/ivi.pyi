from typing import *
from typing_extensions import *

def get_prefer_pyvisa() -> bool: pass
def set_prefer_pyvisa(value: bool = True): pass

def get_index(l: list | dict, i: int) -> int: pass
def get_index_dict(l: list): pass

# TODO: Check what the functions are for
def add_attribute(obj, name, attr, doc = None): pass
def add_method(obj, name, f, doc = None): pass
def add_property(obj, name, fget, fset = None, fdel = None, doc = None): pass
def add_group_capability(obj, cap): pass

def build_ieee_block(data: bytes) -> bytes: pass
def decode_ieee_block(data: bytes) -> bytes: pass

# TODO
def get_sig(sig): pass 
def rms(y): pass

def trim_doc(docstring: str) -> str: pass
def doc(obj, itm, docs, prefix) -> Any: pass
def help(obj, item, complete, indent) -> Any: pass
def list_resources() -> list[str]: pass

class IviDriverOperation:
    cache: bool
    
    driver_setup: Final[str] 
    interchange_check: bool
    logical_name: Final[str]
    query_instrument_status: bool
    range_check: bool
    record_coercions: bool
    io_resource_descriptor: Final[str]
    simulate: Final[str]

    def clear_interchange_warnings(self) -> None: pass
    def get_next_coercion_record(self) -> str: pass
    def get_next_interchange_warning(self) -> str: pass
    def invalidate_all_attributes(self) -> None: pass
    def reset_interchange_check(self) -> None: pass

class DriverOperation:
    driver_operation: IviDriverOperation
    # TODO: private functions

class IviDriverIdentity:
    description: Final[str]
    identifier: Final[str]
    revesion: Final[str]
    vendor: Final[str]
    instrument_manufacturer: Final[str]
    instrument_model: Final[str]
    instrument_firmware_revision: Final[str]
    specification_major_version: Final[int]
    specification_minor_version: Final[int]
    supported_instrument_models: Final[str]
    group_capabilities: Final[str]

    def get_group_capabilities(self) -> list[str]: pass
    def get_supported_instrument_models(self) -> list[str]: pass

class DriverIdentity:
    identity: IviDriverIdentity

class IviInherentAttribute(TypedDict, total=False):
    range_check: bool
    query_instr_status: bool
    cache: bool
    simulate: bool
    record_coercions: bool
    interchange_check: bool
    driver_setup: Any
    prefer_pyvisa: bool

class Driver(DriverIdentity, DriverOperation):
    initialized: Final[bool]

    def initialize(self, **kwargs: Unpack[IviInherentAttribute]) -> None: pass
    def close(self) -> None: pass

    def _get_cache_tag(self, tag: Optional[str] = None, skip: int = 1): pass
    def _get_cache_valid(self, tag: Optional[str] = None, index: int = -1, skip_disable: bool = False): pass
    def _set_cache_valid(self, valid: bool = True, tag: Optional[str] = None, index: int = -1): pass
    def _driver_operation_invalidate_all_attributes(self) -> None: pass
    def _write_raw(self, data: bytes) -> None: pass
    def _read_raw(self, num: int = -1) -> bytes: pass
    def _ask_raw(self, data: bytes, num: int = -1) -> bytes: pass
    def _write(self, data: str | tuple[str, ...] | list[str], encoding: str = "utf-8") -> None: pass
    def _read(self, num: int = -1, encoding: str = "utf-8") -> str: pass
    @overload
    def _ask(self, data: str, num: int = -1, encoding: str = "utf-8") -> str: pass
    @overload
    def _ask(self, data: tuple[str, ...] | list[str], num: int = -1, encoding: str = "utf-8") -> list[str]: pass
    def _ask_for_values(self, msg: str, delim: str = ",", converter: type = float, array: bool = True) -> None: pass # TODO
    def _read_stb(self) -> int: pass 
    def _trigger(self) -> None: pass
    def _clear(self) -> None: pass
    def _local(self) -> None: pass
    def _read_ieee_block(self) -> bytes: pass
    def _ask_for_ieee_block(self, data: str | tuple[str, ...] | list[str], encoding: str = "utf-8") -> bytes: pass
    def _write_ieee_block(self, data: bytes, prefix: str | bytes | None = None, encoding: str = "utf-8") -> None: pass
    def doc(self, obj: Any, itm: Any, docs: Any, prefix: Any) -> Any: pass # TODO
    def help(self, itm: Any, complete: Any, indent: Any) -> Any: pass # TODO
