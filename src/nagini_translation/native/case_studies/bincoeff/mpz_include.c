/*@

fixpoint int bin_mpz(unsigned int n, unsigned int k){
  return ((k == 0) ? 1 :
  ((n == k) ? 1 :
  (bin_mpz((n - 1), (k - 1)) +
  bin_mpz((n - 1), k))));
}
@*/
/*@
lemma_auto void bin_mpz_bod(unsigned int n, unsigned int k);
  requires n >= 0 && k >= 0 && k <= n && n <= 63;
  ensures bin_mpz(n, k) >= 0 && bin_mpz(n, k) <= ULONG_MAX;
  @*/
typedef unsigned long int mp_limb_t;
struct __mpz_struct
{
  int _mp_alloc;    /* Number of *limbs* allocated and pointed
           to by the _mp_d field.  */
  int _mp_size;     /* abs(_mp_size) is the number of limbs the
           last field points to.  If _mp_size is
           negative this is a negative number.  */
  mp_limb_t *_mp_d; /* Pointer to the limbs.  */
};
typedef struct __mpz_struct *mpz_t;
//@predicate is_mpz(mpz_t x; int val);

void mpz_init(mpz_t x);
/*@requires true;@*/
/*@ensures is_mpz(x,_);@*/

void mpz_clear(mpz_t x);
/*@requires is_mpz(x, _);@*/
/*@ensures true;@*/

void mpz_bin_uiui(mpz_t res, unsigned long n, unsigned long k);
/*@requires is_mpz(res,_) &*& n >= 0 &*& k >= 0 &*& k<=n;@*/
/*@ensures is_mpz(res, ?res_val) &*& res_val == bin_mpz(n, k);@*/

unsigned long mpz_get_ui(mpz_t x);
/*@requires is_mpz(x, ?val);@*/
/*@ensures is_mpz(x, val) &*& result == ((val <= ULONG_MAX)?val:(val & ULONG_MAX));@*/
