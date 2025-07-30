#include <cstdint>
#include "fsapper.chh"
#include <filesystem>
#include <vector>
#include <string>
#include <chrono>

namespace fs = std::filesystem;

struct FsIter {
    std::vector<fs::directory_entry> entries;
    size_t index = 0;
};

struct FsEntry {
    fs::directory_entry entry;
    std::string path_cache;
};

FsIter* fs_iter_create(const char* path) {
    FsIter* it = new FsIter();
    try {
        for (const auto& e : fs::directory_iterator(path))
            it->entries.push_back(e);
        return it;
    } catch (...) {
        delete it;
        return nullptr;
    }
}

FsEntry* fs_iter_next(FsIter* iter) {
    if (!iter || iter->index >= iter->entries.size()) return nullptr;
    FsEntry* e = new FsEntry{iter->entries[iter->index++], ""};
    return e;
}

void fs_iter_destroy(FsIter* iter) {
    delete iter;
}

void fs_entry_destroy(FsEntry* entry) {
    delete entry;
}

const char* fs_entry_path(FsEntry* entry) {
    if (!entry) return nullptr;
    entry->path_cache = entry->entry.path().string();
    return entry->path_cache.c_str();
}

bool fs_entry_is_directory(FsEntry* entry) {
    return entry && entry->entry.is_directory();
}

bool fs_entry_is_regular_file(FsEntry* entry) {
    return entry && entry->entry.is_regular_file();
}

bool fs_entry_is_symlink(FsEntry* entry) {
    return entry && entry->entry.is_symlink();
}

bool fs_entry_exists(FsEntry* entry) {
    return entry && entry->entry.exists();
}

uintmax_t fs_entry_file_size(FsEntry* entry) {
    try {
        return fs::file_size(entry->entry.path());
    } catch (...) {
        return 0;
    }
}

int64_t fs_entry_last_write_time(FsEntry* entry) {
    try {
        auto ftime = entry->entry.last_write_time();
        return std::chrono::duration_cast<std::chrono::seconds>(
                   ftime.time_since_epoch()).count();
    } catch (...) {
        return -1;
    }
}
