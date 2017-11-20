# -*- coding: utf-8 -*-
"""Binary line reader file-like object."""

from __future__ import unicode_literals

import os


class BinaryLineReader(object):
  """Line reader for binary file-like objects."""

  # The size of the lines buffer.
  _LINES_BUFFER_SIZE = 1024 * 1024

  # The maximum allowed size of the read buffer.
  _MAXIMUM_READ_BUFFER_SIZE = 16 * 1024 * 1024

  def __init__(self, file_object, end_of_line=b'\n'):
    """Initializes the line reader.

    Args:
      file_object (FileIO): a file-like object to read from.
      end_of_line (Optional[bytes]): end of line indicator.
    """
    super(BinaryLineReader, self).__init__()
    self._file_object = file_object
    self._file_object_size = file_object.get_size()
    self._end_of_line = end_of_line
    self._end_of_line_length = len(self._end_of_line)
    self._lines = []
    self._lines_buffer = b''
    self._lines_buffer_offset = 0
    self._current_offset = 0

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def __iter__(self):
    """Returns a line of text.

    Yields:
      bytes: line of text.
    """
    line = self.readline()
    while line:
      yield line
      line = self.readline()

  # Note: that the following functions do not follow the style guide
  # because they are part of the readline file-like object interface.

  def readline(self, size=None):
    """Reads a single line of text.

    The functions reads one entire line from the file-like object. A trailing
    end-of-line indicator (newline by default) is kept in the byte string (but
    may be absent when a file ends with an incomplete line). An empty byte
    string is returned only when end-of-file is encountered immediately.

    Args:
      size (Optional[int]): maximum byte size to read. If present and
          non-negative, it is a maximum byte count (including the trailing
          end-of-line) and an incomplete line may be returned.

    Returns:
      bytes: line of text.
    """
    if size is not None and size < 0:
      raise ValueError('Invalid size value smaller than zero.')

    if size is not None and size > self._MAXIMUM_READ_BUFFER_SIZE:
      raise ValueError('Invalid size value exceeds maximum.')

    if not self._lines:
      if self._lines_buffer_offset >= self._file_object_size:
        return b''

      read_size = size
      if not read_size:
        read_size = self._MAXIMUM_READ_BUFFER_SIZE

      if self._lines_buffer_offset + read_size > self._file_object_size:
        size = self._file_object_size - self._lines_buffer_offset

      self._file_object.seek(self._lines_buffer_offset, os.SEEK_SET)
      read_buffer = self._file_object.read(size)

      self._lines_buffer_offset += len(read_buffer)

      self._lines = read_buffer.split(self._end_of_line)
      if self._lines_buffer:
        self._lines[0] = b''.join([self._lines_buffer, self._lines[0]])
        self._lines_buffer = b''

      if read_buffer[self._end_of_line_length:] != self._end_of_line:
        self._lines_buffer = self._lines.pop()

      for index, line in enumerate(self._lines):
        self._lines[index] = b''.join([line, self._end_of_line])

      if (self._lines_buffer and
          self._lines_buffer_offset >= self._file_object_size):
        self._lines.append(self._lines_buffer)
        self._lines_buffer = b''

    if not self._lines:
      line = self._lines_buffer
      self._lines_buffer = b''

    elif not size or size >= len(self._lines[0]):
      line = self._lines.pop(0)

    else:
      line = self._lines[0]
      self._lines[0] = line[size:]
      line = line[:size]

    self._current_offset += len(line)

    return line

  def readlines(self, sizehint=None):
    """Reads lines of text.

    The function reads until EOF using readline() and return a list containing
    the lines read.

    Args:
      sizehint (Optional[int]): maximum byte size to read. If present, instead
          of reading up to EOF, whole lines totalling sizehint bytes are read.

    Returns:
      list[bytes]: lines of text.
    """
    if sizehint is None or sizehint <= 0:
      sizehint = None

    lines = []
    lines_byte_size = 0
    line = self.readline()

    while line:
      lines.append(line)

      if sizehint is not None:
        lines_byte_size += len(line)

        if lines_byte_size >= sizehint:
          break

      line = self.readline()

    return lines

  def tell(self):
    """Retrieves the current offset into the file-like object.

    Returns:
      int: cuffent offset into the file-like object.
    """
    return self._current_offset