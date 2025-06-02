include {
    "darrays.sw",
}

extern int strcmp(ptr char, ptr char)

dynamic_array(ptr char, dict_keys)

macro dictionary(val_t, name) {
    dynamic_array(val_t, name@_vals);

    struct name {
        dict_keys keys,
        name@_vals values,
    };
}

macro dt_init(dt) {
    da_init((dt).keys);
    da_init((dt).values);
}

macro dt_make(type, dt) {{
    type dt;
    dt_init(dt);
};}

macro dt_find(dt, key) {
    {
        int idx = 0;
        int found = -1;
    };
    while (idx < (dt).keys.length) {
        if (strcmp((dt).keys.items[idx], key) == 0) {
            found = idx;
            idx = (dt).keys.length;
        };
        idx++;
    };
    found;
}

macro dt_exists(dt, key) { dt_find(dt, key) != -1; }

macro dt_get(dt, key) {
    {
        int at = dt_find(dt, key);
    };
    (dt).values.items[at];
}

macro dt_remove(dt, key) {
    {
        int at = dt_find(dt, key);
    };
    da_remove((dt).keys, at);
    da_remove((dt).values, at);
}

macro dt_add(dt, key, val) {
    da_append((dt).keys, key);
    da_append((dt).values, val);
}


