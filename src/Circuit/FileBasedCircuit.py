from mmap import mmap
from pathlib import Path
from shutil import copyfile
from subprocess import run
from Circuit import Circuit
import Config

COMPILE_CMD = "icepack"

class FileBasedCircuit(Circuit):
    """
    Represents a Circuit that is based on an ASC file, in a format
    ready to be compiled by IceStorm tools.
    This class should not be instantiated but rather extended
    Provides useful methods for working with hardware files
    """

    def __init__(self, index: int, filename: str, config: Config, template: Path):
        Circuit.__init__(index, filename, config)

        asc_dir = config.get_asc_directory()
        bin_dir = config.get_bin_directory()
        data_dir = config.get_data_directory()
        self.__hardware_filepath = asc_dir.joinpath(filename + ".asc")
        self.__bitstream_filepath = bin_dir.joinpath(filename + ".bin")

        # NOTE Using log files instead of a data buffer in the event of premature termination
        self.__data_filepath = data_dir.joinpath(filename + ".log")
        # Create the data file if it doesn't exist
        open(self.__data_filepath, "w").close()

        if template:
            copyfile(template, self.__hardware_filepath)

        # Since the hardware file is written to and read from a lot, we
        # mmap it to improve preformance.
        hardware_file = open(self.__hardware_filepath, "r+")
        self.__hardware_file = mmap(hardware_file.fileno(), 0)
        hardware_file.close()

    def mutate(self):
        def mutate_bit(bit, row, col, *rest):
            if self.__config.get_mutation_probability() >= self.__rand.uniform(0,1):
                # Set this bit to either a 0 or 1 randomly
                # Keep in mind that these are BYTES that we are modifying, not characters
                # Therefore, we have to set it to either ASCII 0 (48) or ASCII 1 (49), not actual 0 or 1, which represent different characters
                # and will corrupt the file if we mutate in this way
                # 48 = 0, 49 = 1. To flip, just need to do (48+49) - the current value (48+49=97)
                # This now always flips the bit instead of randomly assigning it every time
                # Note: If prev != 48 or 49, then we changed the wrong value because it was not a 0 or 1 previously
                #self.__log_event(4, "Mutating:", self, "@(", row, ",", col, ") previous was", bit)
                return 97 - bit
        self.__run_at_each_modifiable(mutate_bit)

    def randomize_bitstream(self):
        def randomize_bit(*rest):
            return self.__rand.integers(48, 50)
        self.__run_at_each_modifiable(randomize_bit)

    def __compile(self):
        """
        Compile circuit ASC file to a BIN file for hardware upload.
        """
        #self.__log_event(2, "Compiling", self, "with icepack...")

        # Ensure the file backing the mmap is up to date with the latest
        # changes to the mmap.
        self.__hardware_file.flush()

        compile_command = [
            COMPILE_CMD,
            self.__hardware_filepath,
            self.__bitstream_filepath
        ]
        run(compile_command)

        #self.__log_event(2, "Finished compiling", self)

    def __run_at_each_modifiable(self, lambda_func, hardware_file = None, accessible_columns = None,
        routing_type=None):
        """
        Runs the lambda_func at every modifiable position
        Args passed to lambda_func: value of bit (as a byte), row, col
        If lambda_func returns a value (byte), then the bit is set to that number
        If lambda_func returns None, then the bit is left unmodified
        Keep in mind the bytes are the ASCII codes, so for example 49 = 1

        .. todo::
            Go over this with someone who can clarify what all of the data types are. 

        Parameters
        ----------
        lambda_func : Callable
            This function is called for each modifiable bit. The bit value is passed into lambda_func.
            If lambda_func returns None, the bit is left unmodified. If lambda_func returns another value,
            then the bit at that position is replaced with the return value of lambda_func.
        hardware_file : str | None
            The path to the hardware file to read from/write to. If no value provided, uses this Circuit's hardware file.
        accessible_columns : list[str] | None
            The accessible columns. If no value provided, uses the current configuration value.
        routing_type: str | None
            The routing type (MOORE or NEWSE). If no value provided, uses the current configuration value.
        """

        if hardware_file is None:
            hardware_file = self.__hardware_file

        if accessible_columns is None:
            accessible_columns = self.__config.get_accessed_columns()

        if routing_type is None:
            routing_type = self.__config.get_routing_type()

        # Set tile to the first location of the substring ".logic_tile"
        # The b prefix makes the string an instance of the "bytes" type
        # The .logic_tile header indicates that there is a tile, so the "tile" variable stores the starting point of the current tile
        tile = hardware_file.find(b".logic_tile")
        
        while tile > 0:
            # Set pos to the position of this tile, but with the length of ".logic_tile" added so it is in front of where we have the x/y coords
            pos = tile + len(".logic_tile")
            
            # Check if the position is legal to modify
            if self.__tile_is_included(hardware_file, pos):
                # Find the start and end of the line; the positions of the \n newline just before and at the end of this line
                # The start is the newline position + 1, so the first valid bit character
                # line_size is self-explanatory
                # This finds the length of a standard line of bits (so the width of each data-containing line in this tile)
                line_start = hardware_file.find(b"\n", tile) + 1
                line_end = hardware_file.find(b"\n", line_start + 1)
                line_size = line_end - line_start + 1

                # Determine which rows we can modify
                # TODO ALIFE2021 The routing protocol here is dated and needs to mimic that of the Tone Discriminator
                if routing_type == "MOORE":
                    rows = [1, 2, 13]
                elif routing_type == "NEWSE":
                    rows = [1, 2]
                # Iterate over each row and the columns that we can access within each row
                for row in rows:
                    for col in accessible_columns:
                        # This will get us to individual bits. If the mutation probability passes
                        # Our position is now going to be the start of the first line, plus the line size multiplied to get to our desired row,
                        # and finally added to the column (with the int cast to sanitize user input)
                        pos = line_start + line_size * (row - 1) + int(col)
                        bit_value = hardware_file[pos]
                        lambda_return = lambda_func(bit_value, row, col)
                        if lambda_return is not None:
                            # need to re-assign the bit
                            hardware_file[pos] = lambda_return

            # Find the next logic tile, and start again
            # Will return -1 if .logic_tile isn't found, and the while loop will exit
            tile = hardware_file.find(b".logic_tile", tile + 1)