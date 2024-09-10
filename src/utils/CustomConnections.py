import nest


def connect(
    pre,
    post,
    conn_spec=None,
    syn_spec=None,
    return_synapsecollection=False,
    num_sources=None,
):
    if conn_spec == "x_to_one":
        if num_sources is None:
            raise Exception(
                "when using custom conn_spec 'x_to_one' argument 'num_sources' must be set"
            )
        assert num_sources is not None
        for i in range(len(post)):
            nest.Connect(
                pre[num_sources * i : num_sources * (i + 1)],
                post[i],
                "all_to_all",
                syn_spec,
                return_synapsecollection,
            )
    else:
        nest.Connect(pre, post, conn_spec, syn_spec, return_synapsecollection)
