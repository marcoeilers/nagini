def test_bool() -> None:
  assert bool(float('nan')) == True
  assert bool(1.0) == True
  assert bool(0.0) == False
  assert bool(-1.0) == True
  assert bool(float('inf')) == True
  assert bool(float('-inf')) == True

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_nan_float_compare() -> None:
  assert (float('nan') >= 1.0) == False
  assert (float('nan') >= 0.0) == False
  assert (float('nan') >= -1.0) == False
  assert (1.0 >= float('nan')) == False
  assert (0.0 >= float('nan')) == False
  assert (-1.0 >= float('nan')) == False
  assert (float('nan') >= float('nan')) == False
  
  assert (float('nan') > 1.0) == False
  assert (float('nan') > 0.0) == False
  assert (float('nan') > -1.0) == False
  assert (1.0 > float('nan')) == False
  assert (0.0 > float('nan')) == False
  assert (-1.0 > float('nan')) == False
  assert (float('nan') > float('nan')) == False
  
  assert (float('nan') <= 1.0) == False
  assert (float('nan') <= 0.0) == False
  assert (float('nan') <= -1.0) == False
  assert (1.0 <= float('nan')) == False
  assert (0.0 <= float('nan')) == False
  assert (-1.0 <= float('nan')) == False
  assert (float('nan') <= float('nan')) == False
  
  assert (float('nan') < 1.0) == False
  assert (float('nan') < 0.0) == False
  assert (float('nan') < -1.0) == False
  assert (1.0 < float('nan')) == False
  assert (0.0 < float('nan')) == False
  assert (-1.0 < float('nan')) == False
  assert (float('nan') < float('nan')) == False
  
  assert (float('nan') == 1.0) == False
  assert (float('nan') == 0.0) == False
  assert (float('nan') == -1.0) == False
  assert (1.0 ==  float('nan')) == False
  assert (0.0 ==  float('nan')) == False
  assert (-1.0 == float('nan')) == False
  assert (float('nan') == float('nan')) == False

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False



def test_nan_int_compare() -> None:
  assert (float('nan') >= 1) == False
  assert (float('nan') >= 0) == False
  assert (float('nan') >= -1) == False
  assert (1 >= float('nan')) == False
  assert (0 >= float('nan')) == False
  assert (-1 >= float('nan')) == False
  
  assert (float('nan') > 1) == False
  assert (float('nan') > 0) == False
  assert (float('nan') > -1) == False
  assert (1 > float('nan')) == False
  assert (0 > float('nan')) == False
  assert (-1 > float('nan')) == False
  
  assert (float('nan') <= 1) == False
  assert (float('nan') <= 0) == False
  assert (float('nan') <= -1) == False
  assert (1 <= float('nan')) == False
  assert (0 <= float('nan')) == False
  assert (-1 <= float('nan')) == False
  
  assert (float('nan') < 1) == False
  assert (float('nan') < 0) == False
  assert (float('nan') < -1) == False
  assert (1 < float('nan')) == False
  assert (0 < float('nan')) == False
  assert (-1 < float('nan')) == False
  
  assert (float('nan') == 1) == False
  assert (float('nan') == 0) == False
  assert (float('nan') == -1) == False
  assert (1 ==  float('nan')) == False
  assert (0 ==  float('nan')) == False
  assert (-1 == float('nan')) == False

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_inf_compare() -> None:
  assert (float('inf') > float('inf')) == False
  assert (float('inf') > 0.0) == True
  assert (float('inf') > 0) == True
  assert (float('inf') > float('-inf')) == True
  
  assert (float('inf') >= float('inf')) == True
  assert (float('inf') >= 0.0) == True
  assert (float('inf') >= 0) == True
  assert (float('inf') >= float('-inf')) == True
  
  assert (float('inf') < float('inf')) == False
  assert (float('inf') < 0.0) == False
  assert (float('inf') < 0) == False
  assert (float('inf') < float('-inf')) == False
  
  assert (float('inf') <= float('inf')) == True
  assert (float('inf') <= 0.0) == False
  assert (float('inf') < 0) == False
  assert (float('inf') <= float('-inf')) == False
  
  assert (float('inf') == float('inf')) == True
  assert (float('inf') == 0.0) == False
  assert (float('inf') == 0) == False
  assert (float('inf') == float('-inf')) == False

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False
  
def test_neg_inf_compare() -> None:
  assert (float('-inf') > float('inf')) == False
  assert (float('-inf') > 0.0) == False
  assert (float('-inf') > 0) == False
  assert (float('-inf') > float('-inf')) == False
  
  assert (float('-inf') >= float('inf')) == False
  assert (float('-inf') >= 0.0) == False
  assert (float('-inf') >= 0) == False
  assert (float('-inf') >= float('-inf')) == True
  
  assert (float('-inf') < float('inf')) == True
  assert (float('-inf') < 0.0) == True
  assert (float('-inf') < 0) == True
  assert (float('-inf') < float('-inf')) == False
  
  assert (float('-inf') <= float('inf')) == True
  assert (float('-inf') <= 0.0) == True
  assert (float('-inf') <= 0) == True
  assert (float('-inf') <= float('-inf')) == True
  
  assert (float('-inf') == float('inf')) == False
  assert (float('-inf') == 0.0) == False
  assert (float('-inf') == 0) == False
  assert (float('-inf') == float('-inf')) == True

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_add() -> None:
  inf = float('inf')
  ninf = float('-inf')
  assert 1.2 + 1.3 == 2.5
  assert 1.0 + inf == inf
  assert inf + 1.0 == inf
  assert ninf + 1.0 == ninf
  assert 1.0 + ninf == ninf
  assert inf + inf == inf
  assert ninf + ninf == ninf
  assert inf + ninf is float('nan')
  assert ninf + inf is float('nan')
  assert inf + float('nan') is float('nan')
  assert float('nan') + inf is float('nan')
  assert ninf + float('nan') is float('nan')
  assert float('nan') + ninf is float('nan')
  assert float('nan') + 1.0 is float('nan')
  assert 1.0 + float('nan') is float('nan')
  assert float('nan') + float('nan') is float('nan')

  assert 1 + 1.5 == 2.5
  assert 1 + inf == inf
  assert inf + 1 == inf
  assert ninf + 1 == ninf
  assert 1 + ninf == ninf
  assert float('nan') + 1 is float('nan')
  assert 1 + float('nan') is float('nan')

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_subtract() -> None:
  inf = float('inf')
  ninf = float('-inf')
  assert 2.0 - 0.5 == 1.5
  assert 1.0 - inf == ninf
  assert inf - 1.0 == inf
  assert ninf - 1.0 == ninf
  assert 1.0 - ninf == inf
  assert inf - inf is float('nan')
  assert ninf - ninf is float('nan')
  assert inf - ninf == inf
  assert ninf - inf == ninf
  assert inf - float('nan') is float('nan')
  assert float('nan') - inf is float('nan')
  assert ninf - float('nan') is float('nan')
  assert float('nan') - ninf is float('nan')
  assert float('nan') - 1.0 is float('nan')
  assert 1.0 - float('nan') is float('nan')
  assert float('nan') - float('nan') is float('nan')

  assert 1 - 1.5 == -0.5
  assert 1 - inf == ninf
  assert inf - 1 == inf
  assert ninf - 1 == ninf
  assert 1 - ninf == inf
  assert float('nan') - 1 is float('nan')
  assert 1 - float('nan') is float('nan')

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_multiply() -> None:
  inf = float('inf')
  ninf = float('-inf')
  assert 1.5 * -2.0 == -3
  assert 1.0 * inf == inf
  assert inf * 1.0 == inf
  assert -1.0 * inf == ninf
  assert inf * -1.0 == ninf
  assert ninf * 1.0 == ninf
  assert 1.0 * ninf == ninf
  assert -1.0 * ninf == inf
  assert ninf * -1.0 == inf
  assert 0.0 * inf is float('nan')
  assert inf * 0.0 is float('nan')
  assert 0.0 * ninf is float('nan')
  assert ninf * 0.0 is float('nan')
  assert inf * inf == inf
  assert ninf * ninf == inf
  assert inf * ninf == ninf
  assert ninf * inf == ninf
  assert inf * float('nan') is float('nan')
  assert float('nan') * inf is float('nan')
  assert ninf * float('nan') is float('nan')
  assert float('nan') * ninf is float('nan')
  assert float('nan') * 1.0 is float('nan')
  assert 1.0 * float('nan') is float('nan')
  assert float('nan') * float('nan') is float('nan')

  assert 1 * -2.0 == -2
  assert 1 * inf == inf
  assert inf * 1 == inf
  assert -1 * inf == ninf
  assert inf * -1 == ninf
  assert ninf * 1 == ninf
  assert 1 * ninf == ninf
  assert -1 * ninf == inf
  assert ninf * -1 == inf
  assert 0 * inf is float('nan')
  assert inf * 0 is float('nan')
  assert 0 * ninf is float('nan')
  assert ninf * 0 is float('nan')
  assert float('nan') * 1 is float('nan')
  assert 1 * float('nan') is float('nan')

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False

def test_divide() -> None:
  inf = float('inf')
  ninf = float('-inf')
  assert 2.5 / 5.0 == 0.5
  assert 1.0 / inf == 0.0
  assert inf / 1.0 == inf
  assert -1.0 / inf == 0.0
  assert inf / -1.0 == ninf
  assert ninf / 1.0 == ninf
  assert 1.0 / ninf == 0.0
  assert ninf / -1.0 == inf
  assert -1.0 / ninf == 0.0
  assert inf / inf is float('nan')
  assert ninf / ninf is float('nan')
  assert inf / ninf is float('nan')
  assert ninf / inf is float('nan')
  assert inf / float('nan') is float('nan')
  assert float('nan') / inf is float('nan')
  assert ninf / float('nan') is float('nan')
  assert float('nan') / ninf is float('nan')
  assert float('nan') / 1.0 is float('nan')
  assert 1.0 / float('nan') is float('nan')
  assert float('nan') / float('nan') is float('nan')

  assert 2.5 / 5 == 0.5
  assert 1 / inf == 0
  assert inf / 1 == inf
  assert -1 / inf == 0
  assert inf / -1 == ninf
  assert ninf / 1 == ninf
  assert 1 / ninf == 0
  assert ninf / -1 == inf
  assert -1 / ninf == 0
  assert float('nan') / 1 is float('nan')
  assert 1 / float('nan') is float('nan')

  #:: ExpectedOutput(assert.failed:assertion.false)
  assert False