import hashlib as hl


def calc_hash(str_data):
    # hash = hl.sha256(str_data.encode()).hexdigest()
    # print("Hash: " + hash + " <<== Str Data: " + str_data)
    # return hash
    return hl.sha256(str_data.encode()).hexdigest()


