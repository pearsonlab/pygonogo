import json

def load_pars(fname):
    # load parameters from a json file
    with open(fname) as fp:
        pars = json.load(fp)

    return pars
