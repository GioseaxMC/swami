@windows param "<libs>/fsapper.o -lstdc++ -lstdc++fs"
@linux param "<libs>/fsapper-linux.o -lstdc++ -lstdc++fs"

extern ptr void fs_iter_create(ptr char)                # Create a directory iterator for the given path (returns opaque pointer)
extern ptr void fs_iter_next(ptr void)                  # Advance the iterator and return the next entry (returns opaque entry or null)
extern void fs_iter_destroy(ptr void)                   # Free the iterator and all associated resources

macro make_entries(name) { fs_iter_create(name); }
macro next_entry(iter) { fs_iter_next(iter); }
macro free_entries(iter) { fs_iter_destroy(iter); }

extern void fs_entry_destroy(ptr void)                  # Free the memory used by a directory entry
extern ptr char fs_entry_path(ptr void)                 # Get the path of the current entry (valid until the next call)
extern bool fs_entry_is_directory(ptr void)             # True if the entry is a directory
extern bool fs_entry_is_regular_file(ptr void)          # True if the entry is a regular file
extern bool fs_entry_is_symlink(ptr void)               # True if the entry is a symbolic link
extern bool fs_entry_exists(ptr void)                   # True if the entry exists (non-dangling symlink, etc.)

extern i64 fs_entry_file_size(ptr void)                 # Get the file size in bytes
extern i64 fs_entry_last_write_time(ptr void)           # Get the last write timestamp (as UNIX epoch in seconds)

macro free_entry(entry) { fs_entry_destroy(entry); }
macro entry_path(entry) { fs_entry_path(entry); }
macro entry_is_dir(entry) { fs_entry_is_directory(entry); }
macro entry_is_file(entry) { fs_entry_is_regular_file(entry); }
macro entry_is_symlink(entry) { fs_entry_is_symlink(entry); }
macro entry_exists(entry) { fs_entry_exists(entry); }

macro entry_file_size(entry) { fs_entry_file_size(entry); }
