macro store_of(type) {
    struct type@Store {
        type value,
        bool lock,
    };
}

macro st_wait_with(store, block) {
    while ((store).lock)
        block;
}

macro st_wait(store) {
    st_wait_with(store,{});
}

macro st_raw(store) {
    (store).value;
}

macro st_read(store) {
    st_wait(store);
    st_raw(store);
}

macro st_lock(store) { # please make sure to st_unlock after using this
    st_wait(store);
    (store).lock = 1;
}

macro st_unlock(store) {
    (store).lock = 0;
}

macro st_subscribe(store, name, body) {
    macro __st_subscribe(store, name) {
        st_wait(store);
        st_lock(store);
        body;
        st_unlock(store);
    };
    __st_subscribe(store, (store).value);
}
