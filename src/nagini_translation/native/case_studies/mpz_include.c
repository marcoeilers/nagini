//#include <gmp.h>

typedef unsigned long int	mp_limb_t;
typedef struct
{
  int _mp_alloc;		/* Number of *limbs* allocated and pointed
				   to by the _mp_d field.  */
  int _mp_size;			/* abs(_mp_size) is the number of limbs the
				   last field points to.  If _mp_size is
				   negative this is a negative number.  */
  mp_limb_t *_mp_d;		/* Pointer to the limbs.  */
} __mpz_struct;
typedef __mpz_struct* mpz_t;
//@predicate is_mpz(mpz_t x; int val);

void mpz_init(mpz_t x);
/*@requires true;@*/
/*@ensures is_mpz(x,_);@*/

/*@
fixpoint unsigned int bincoeff(unsigned int n, unsigned int k) {
    return (k == 0) ? 1 :
           (n == 0) ? 0 :
           bincoeff(n-1, k-1) + bincoeff(n-1, k);
}
@*/
void mpz_bin_uiui(mpz_t res, unsigned int n, unsigned int k);
/*@requires is_mpz(res,_) &*& n >= 0 &*& k >= 0 &*& k<=n;@*/
/*@ensures is_mpz(res, ?res_val) &*& res_val == bincoeff(n, k);@*/