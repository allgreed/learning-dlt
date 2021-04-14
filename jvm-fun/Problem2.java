public class Problem2 {
   public static void main(String[] args) {
       long t1 = System.nanoTime();
       loop();
       long t2 = System.nanoTime();
       loop_unroll();
       long t3 = System.nanoTime();

       System.out.println(t2 - t1);
       System.out.println(t3 - t2);
       // Loop unroll is consistently ~3x times faster
       // yet the code for unroll is ~50% bigger
   }

   public static int loop() {
        int k = 0;
        for( int i = 0; i < 10; i++ ) {
            k += i;
        }
        return k;
   }

   public static int loop_unroll() {
        int k = 0;
        k += 0;
        k += 1;
        k += 2;
        k += 3;
        k += 4;
        k += 5;
        k += 6;
        k += 7;
        k += 8;
        k += 9;
        return k;
   }
}
