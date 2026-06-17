import factor

def test_betas_shape_and_columns(warehouse):
    betas = factor.compute_betas(warehouse)
    assert set(["ticker", "beta", "alpha_daily"]).issubset(betas.columns)
    assert len(betas) == 6

def test_average_beta_near_one(warehouse):
    # betas are relative to the equal-weight market, so they should average ~1
    betas = factor.compute_betas(warehouse)
    assert 0.7 < betas.beta.mean() < 1.3
