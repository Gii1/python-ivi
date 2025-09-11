"""

Python Interchangeable Virtual Instrument Library

Copyright (c) 2012-2017 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
import ivi
import ivi.fgen as fgen
import ivi.scpi.common as scpi
import numpy as np

OperationModeMapping = ["burst", "continuous"]
OutputModeMapping = {"function": "FIX", "arbitrary": "USER", "sequence": "SEQ", "advanced_sequence": "ASEQ", "modulated": "MOD", "pulse": "PULS"}
ReferenceClockSourceMapping = {"internal": "INT", "external": "EXT"}
SyncFunctionMapping = {"pulse": "PULS", "waveform_complete": "WCOM"}

class agilent81180a(scpi.IdnCommand, scpi.ErrorQuery, scpi.Reset, ivi.Driver, fgen.Base, fgen.StdFunc, fgen.ArbWfm, fgen.ArbFrequency, fgen.ArbSeq, fgen.ArbChannelWfm):
    """Agilent 81180A arbitary waveform generator driver"""

    def __init__(self, *args, **kwargs):
        """Default port: 5025"""        
        super().__init__(*args, **kwargs)
                
        self._output_count = 2

        # for fgen.ArbWfm
        self._arbitrary_waveform_number_waveforms_max = 32000
        self._arbitrary_waveform_size_max = 16000000
        self._arbitrary_waveform_size_min = 320
        self._arbitrary_waveform_quantum = 32
        
        # for fgen.ArbSeq
        self._arbitrary_sequence_number_sequences_max = 1000
        self._arbitrary_sequence_loop_count_max = 1048575
        self._arbitrary_sequence_length_max = 32768
        self._arbitrary_sequence_length_min = 3

        # fgen.SparseMarker
        self._sparse_marker_count = 1

        # general
        self._identity_description = "Agilent 81180A arbitary waveform generator driver"
        self._identity_identifier = ""
        self._identity_revision = ""
        self._identity_vendor = ""
        self._identity_instrument_manufacturer = "Agilent Technolgies"
        self._identity_instrument_model = ""
        self._identity_instrument_firmware_revision = ""
        self._identity_specification_major_version = 1
        self._identity_specification_minor_version = 0
        self._identity_supported_instrument_models = ["81180A"]

        # sync functionality
        self._add_property("sync.function",
                        self._get_sync_function, self._set_sync_function, None, 
                        """
                        Specifies the shape of the sync pulse. This property can be either pulse 
                        or wave_complete.
                        """)
        self._add_property("outputs[].sync.position", 
                        self._get_output_sync_position, self._set_output_sync_position, None,
                        """
                        Specifies the position relative to the start of the sync pulse. The 
                        position can be programmed in increments of 32 points up to the maximum 
                        of the wavelength. Only has an effect in arbitrary mode.
                        """)
        self._add_property("outputs[].sync.width",
                        self._get_output_sync_width, self._set_output_sync_width, None, 
                        """
                        Specifies the width of the sync pulse. The sync width can be programmed
                        in increments of 32 points up to the maximum of the wavelength. Only has
                        an effect in arbitrary mode.""")
        self._add_property("sync.source", 
                        self._get_sync_source, self._set_sync_source, None,
                        """
                        Specifies the source channel for the sync pulse.
                        """)
        self._add_property("sync.enabled", 
                        self._get_sync_enabled, self._set_sync_enabled, None, 
                        """
                        If set to True, the function generator produces the sync pulse at the
                        sync out at the front panel. If set to False, the signal does not appear 
                        at the connector.                        
                        """)
        
        self._sync_function = "pulse"
        self._sync_source = 0
        self._sync_enabled = False

        # device specific
        self._selected_channel = 0
        self._segment_count = [0, 0] # TODO: Sync with AWG
        self._sequence_count = 0

        self._init_outputs()
    
    def _initialize(self, resource = None, id_query = False, reset = False, **keywargs):
        "Opens an I/O session to the instrument."
        
        super()._initialize(resource, id_query, reset, **keywargs)
        
        # interface clear
        if not self._driver_operation_simulate:
            self._clear()
        
        # check ID
        if id_query and not self._driver_operation_simulate:
            id = self.identity.instrument_model
            id_check = self._instrument_id
            id_short = id[:len(id_check)]
            if id_short != id_check:
                raise Exception("Instrument ID mismatch, expecting %s, got %s", id_check, id_short)
        
        # reset
        if reset:
            self.utility_reset()

    def _init_outputs(self) -> None:
        try:
            super(agilent81180a, self)._init_outputs()
        except AttributeError:
            pass

        self._output_sync_position = [0] * self._output_count
        self._output_sync_width = [32] * self._output_count

        self.outputs._set_list(self._output_name)

    # agilent81180a specific commands
    def _get_selected_channel(self) -> int:
        if not self._driver_operation_simulate and not self._get_cache_valid():
            resp = self._ask(":INST?")
            self._selected_channel = int(resp) - 1
            self._set_cache_valid()

        return self._selected_channel
    
    def _set_selected_channel(self, index: int) -> None:
        if not self._driver_operation_simulate and index != self._get_selected_channel():
            self._write(f":INST {index+1}")
            self._set_cache_valid()
            
        self._selected_channel = index

    def _write_channel(self, data: str, index: int): 
        self._set_selected_channel(index)
        self._write(data)

    def _ask_channel(self, data: str, index: int) -> str:
        self._set_selected_channel(index)
        return self._ask(data)

    # general device function
    def _utility_disable(self): ...
    def _utility_lock_object(self): ...
    
    def _utility_self_test(self): ...    
    def _utility_unlock_object(self): ...    

    # Functions for fgen
    def _get_output_operation_mode(self, index) -> str: 
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":INIT:CONT?", index)
            self._output_operation_mode[index] = OperationModeMapping[int(resp)]
            self._set_cache_valid(index=index)
        return self._output_operation_mode[index]
    
    def _set_output_operation_mode(self, index, value: str):
        index = ivi.get_index(self._output_name, index)
        if value not in OperationModeMapping:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write_channel(f":INIT:CONT {OperationModeMapping.index(value)}", index)
        self._output_operation_mode[index] = value
        self._set_cache_valid(index=index)

    def _get_output_enabled(self, index) -> bool: 
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":OUTP?", index)
            self._output_enabled[index] = bool(resp)
            self._set_cache_valid(index=index)
        return self._output_enabled[index]

    def _set_output_enabled(self, index, value: bool):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate:
            self._write_channel(f":OUTP {int(value)}", index)
        self._output_enabled[index] = value
        self._set_cache_valid(index=index)

    def _get_output_impedance(self, index) -> float: 
        return 50.0 # only has one 
    
    def _set_output_impedance(self, index, value: float) -> None:
        if value != 50.0:
            raise ivi.ValueNotSupportedException()
    
    def _get_output_mode(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":FUNC:MODE?", index)
            self._output_mode[index] = next(key for key, value in OutputModeMapping if value == resp)
            self._set_cache_valid(index=index)
        return self._output_mode[index]

    def _set_output_mode(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value not in OutputModeMapping.keys():
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write_channel(f":FUNC:MODE {OutputModeMapping[value]}", index)
        self._output_mode[index] = value
        self._set_cache_valid(index=index)

    def _get_output_reference_clock_source(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":FREQ:RAST:SOUR?", index)
            self._output_reference_clock_source[index] = next(key for key, value in ReferenceClockSourceMapping if value == resp)
            self._set_cache_valid(index=index)
        return self._output_reference_clock_source[index]

    def _set_output_reference_clock_source(self, index, value): 
        index = ivi.get_index(self._output_name, index)
        if value not in ReferenceClockSourceMapping.keys():
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write_channel(f":FREQ:RAST:SOUR {ReferenceClockSourceMapping[value]}", index)
        self._output_reference_clock_source[index] = value
        self._set_cache_valid(index=index)
 
    def abort_generation(self):  # TODO: Check if independet of channel
        if not self._driver_operation_simulate:
            self._write(":ABOR")

    def initiate_generation(self): # TODO: Check if independet of channel
        if not self._driver_operation_simulate:
            self._write(":ENAB")

    # Functions for fgen.StdFunc
    def _get_output_standard_waveform_amplitude(self, index):  ...
    def _set_output_standard_waveform_amplitude(self, index, value): ...
    def _get_output_standard_waveform_dc_offset(self, index): ...
    def _set_output_standard_waveform_dc_offset(self, index, value): ...
    def _get_output_standard_waveform_duty_cycle_high(self, index): ...
    def _set_output_standard_waveform_duty_cycle_high(self, index, value): ...
    def _get_output_standard_waveform_start_phase(self, index): ...
    def _set_output_standard_waveform_start_phase(self, index, value): ...
    def _get_output_standard_waveform_frequency(self, index): ...
    def _set_output_standard_waveform_frequency(self, index, value): ...
    def _get_output_standard_waveform_waveform(self, index): ...
    def _set_output_standard_waveform_waveform(self, index, value): ...
    
    # for fgen.ArbWfm
    def _get_output_arbitrary_gain(self, index) -> float: 
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":VOLT?", index)
            self._output_arbitrary_gain[index] = float(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_gain[index]

    def _set_output_arbitrary_gain(self, index, value: float):
        index = ivi.get_index(self._output_name, index)
        if not 50e-3 <= value <= 2: # TODO: test how it interacts with offset
            raise ivi.OutOfRangeException() 
        if not self._driver_operation_simulate:
            self._write_channel(f":VOLT {value:.3f}", index)
        self._output_arbitrary_gain[index] = value
        self._set_cache_valid(index=index)

    def _get_output_arbitrary_offset(self, index) -> float:
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":VOLT:OFF?", index)
            self._output_arbitrary_offset[index] = float(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_offset[index]

    def _set_output_arbitrary_offset(self, index, value: float):
        index = ivi.get_index(self._output_name, index)
        if not -1.5 <= value <= 1.5:
            raise ivi.OutOfRangeException() 
        if not self._driver_operation_simulate:
            self._write_channel(f":VOLT:OFFS {value:.3f}", index)
        self._output_arbitrary_offset[index] = value
        self._set_cache_valid(index=index)

    def _get_output_arbitrary_waveform(self, index) -> int: 
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":TRAC:SEL?", index)
            self._output_arbitrary_waveform[index] = int(resp) + index * self._arbitrary_waveform_number_waveforms_max
            self._set_cache_valid(index=index)
        return self._output_arbitrary_waveform[index]

    def _set_output_arbitrary_waveform(self, index, value: int) -> None:
        index = ivi.get_index(self._output_name, index)
        if index != value // self._arbitrary_waveform_number_waveforms_max:
            raise ivi.OutOfRangeException() # Throw error if handle of different channel is used or if waveform is out of range # TODO: Check if the waveform exist on the AWG
        if not self._driver_operation_simulate:
            self._write_channel(f":TRAC:SEL {value % self._arbitrary_waveform_number_waveforms_max}", index)
        self._output_arbitrary_waveform[index] = value
        self._set_cache_valid(index=index)

    def _get_arbitrary_sample_rate(self) -> float:
        if not self._get_cache_valid():
            channel_samplerate = [self.outputs[index].arbitrary.frequency for index in range(self._output_count)]
            if len(set(channel_samplerate)) != 1:
                raise ivi.OperationNotSupportedException()
            self._arbitrary_sample_rate = channel_samplerate[0]
            self._set_cache_valid()
        return self._arbitrary_sample_rate

    def _set_arbitrary_sample_rate(self, value: float) -> None: 
        for index in range(self._output_count):
            self.outputs[index].arbitrary.frequency = value
        self._arbitrary_sample_rate = value
        self._set_cache_valid()

    def _arbitrary_waveform_clear(self, handle: int) -> None:
        index = handle // self._arbitrary_waveform_number_waveforms_max
        if not self._driver_operation_simulate:
            self._write_channel(f":TRAC:DEL {handle}", index)
        if handle == self._segment_count[index]: 
            self._segment_count[index] -= 1 # free segement if it is the last one

    def _arbitrary_waveform_create(self, data: np.typing.ArrayLike) -> int: # TODO: Create dictionary to map handle to actual sequence number and channel, than should be possible to implement
        raise ivi.OperationNotSupportedException()
    
    # fgen.ArbFrequency # TODO: Implementation is wrong, sets samplerate instead of frequency
    def _get_output_arbitrary_frequency(self, index):
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":FREQ:RAST?", index=index)
            self._output_arbitrary_frequency[index] = float(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_frequency[index]

    def _set_output_arbitrary_frequency(self, index, value):
        if not 10e6 <= value <= 4.2e9:
            raise ivi.OutOfRangeException() 
        if not self._driver_operation_simulate:
            self._write_channel(f":FREQ:RAST {value:.3f}", index)
        self._output_arbitrary_frequency = value
        self._set_cache_valid(index=index)
    
    # fgen.ArbSeq
    def _arbitrary_clear_memory(self) -> None:
        if not self._driver_operation_simulate:
            self._write(":TRAC:DEL:ALL")
            self._write(":SEQ:DEL:ALL")
    
    def _arbitrary_sequence_clear(self, handle: int) -> None:
        if not self._driver_operation_simulate:
            self._write(f":SEQ:DEL {handle}")
        if handle == self._sequence_count: 
            self._sequence_count -= 1 # free sequence if it is the last one

    def _get_output_arbitrary_sequence_handle(self, index) -> int:
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask_channel(":SEQ:SEL", index)
            self._output_arbitrary_sequence_handle[index] = int(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_sequence_handle[index]
    
    def _set_output_arbitrary_sequence_handle(self, index, value: int) -> None: # TODO: Add check that handle exist
        if not self._driver_operation_simulate:
            self._write_channel(f":SEQ:SEL {value}", index)
        self._output_arbitrary_sequence_handle[index] = value
        self._set_cache_valid(index=index)
     
    def _arbitrary_sequence_create(self, handle_list: list[int], loop_count_list: list[int]) -> int: # TODO: use binary transport, not important # TODO: Check that handles are valid
        # check for invalid list length
        if len(handle_list) != len(loop_count_list) != 0:
            raise ivi.ValueNotSupportedException()
        
        # sequence has to be at least 3 steps, try to expand if len(handle_list) < 3
        if len(handle_list) < 3:
            if len(handle_list) == 2 and loop_count_list[0] > 1:
                handle_list.insert(1, handle_list[0])
                loop_count_list[0] -= 1
                loop_count_list.insert(1, 1)
            elif len(handle_list) == 2 and loop_count_list[1] > 1:
                handle_list.insert(2, handle_list[1])
                loop_count_list[1] -= 1
                loop_count_list.insert(2, 1)
            elif len(handle_list) == 1 and loop_count_list[0] > 2:
                handle_list.extend([handle_list[0], handle_list[0]])
                loop_count_list[0] -= 2
                loop_count_list.extend([1, 1])

        self._sequence_count += 1

        for index in range(2):
            self._write_channel(f":SEQ:SEL {self._sequence_count}", index)
            self._write_channel(f":SEQ:LENG {len(handle_list)}", index)
            for i in range(len(handle_list)):
                self._write_channel(f":SEQ:DEF {i+1},{handle_list[i]},{loop_count_list[i]},0", index)
            self._set_cache_valid(valid=False, tag="output_arbitrary_sequence_handle", index=index)

        return self._sequence_count

    # for fgen.SoftwareTrigger
    def send_software_trigger(self): ...

    # for fgen.Burst    
    def _get_output_burst_count(self, index): ...    
    def _set_output_burst_count(self, index, value): ...    

    # for fgen.ArbChannelWfm
    def _arbitrary_waveform_create_channel_waveform(self, index, data: np.typing.ArrayLike) -> int: # TODO: Protect from too much data
        data = np.array(data)

        # check if space is still left in the AWG
        if self._segment_count[index] >= self._arbitrary_waveform_number_waveforms_max:
            raise fgen.NoWaveformsAvailableException()

        # check data
        if len(data) < self._arbitrary_waveform_size_min or len(data) % self._arbitrary_waveform_quantum != 0:
            raise ivi.ValueNotSupportedException()
        if not np.all((-1 <= data) & (data <= 1)):
            raise ivi.OutOfRangeException()
        
        self._segment_count[index] += 1
        self._set_selected_channel(index)
        if not self._driver_operation_simulate:
            scaled_data = (np.round(data * 2047) + 2048).astype("<u2").tobytes()
            self._write(f":TRAC:DEF {self._segment_count[index]},{len(data)}")
            self._write(f":TRAC:SEL {self._segment_count[index]}")
            self._write_ieee_block(scaled_data, prefix=":TRAC:DATA ")

        return self._segment_count[index] + index * self._arbitrary_waveform_number_waveforms_max
    
    # sync
    def _get_sync_function(self) -> str:
        if not self._driver_operation_simulate and not self._get_cache_valid():
            resp = self._ask(":OUTP:SYNC:FUNC?")
            self._sync_function = next(key for key, value in SyncFunctionMapping if value == resp)
            self._set_cache_valid()
        return self._sync_function

    def _set_sync_function(self, value: str) -> None:
        if not value in SyncFunctionMapping.keys():
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write(f":OUTP:SYNC:FUNC {SyncFunctionMapping[value]}")
        self._sync_function = value
        self._set_cache_valid()

    def _get_output_sync_position(self, index) -> int:
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":OUTP:SYNC:POS?")
            self._output_sync_position[index] = int(resp)
            self._set_cache_valid(index=index)
        return self._output_sync_position[index]
    
    def _set_output_sync_position(self, index, value: int) -> None: # TODO: Error when longer than waveform
        index = ivi.get_index(self._output_name, index)
        if value % 32 != 0:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write_channel(f":OUTP:SYNC:POS {value}", index)
        self._output_sync_position[index] = value
        self._set_cache_valid(index=index)

    def _get_output_sync_width(self, index) -> int:
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":OUTP:SYNC:WIDT?")
            self._output_sync_width[index] = int(resp)
            self._set_cache_valid(index=index)
        return self._output_sync_width[index]

    def _set_output_sync_width(self, index, value: int) -> None: # TODO: Error when longer than waveform
        index = ivi.get_index(self._output_name, index)
        if value % 32 != 0:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write_channel(f":OUTP:SYNC:WIDT {value}", index)
        self._output_sync_width[index] = value
        self._set_cache_valid(index=index)

    def _get_sync_source(self) -> int:
        if not self._driver_operation_simulate and not self._get_cache_valid():
            resp = self._ask(":OUTP:SYNC:SOUR?")
            self._sync_source = int(resp[2]) - 1
            self._set_cache_valid()
        return self._sync_source

    def _set_sync_source(self, value) -> None:
        value = ivi.get_index(self._output_name, value)
        if not self._driver_operation_simulate:
            self._write(f":OUTP:SYNC:SOUR {value + 1}")
        self._sync_source = value
        self._set_cache_valid()

    def _get_sync_enabled(self) -> bool: 
        if not self._driver_operation_simulate and not self._get_cache_valid():
            resp = self._ask(":OUTP:SYNC?")
            self._sync_enabled = bool(int(resp))
            self._set_cache_valid()
        return self._sync_enabled

    def _set_sync_enabled(self, value: bool) -> None:
        if not self._driver_operation_simulate:
            self._write(f":OUTP:SYNC {int(value)}")
        self._sync_enabled = value
        self._set_cache_valid()

