public class Problem3 {
   public static void main(String[] args) {
       long t1 = System.nanoTime();
       int_native();
       long t2 = System.nanoTime();
       int_boxed();
       long t3 = System.nanoTime();

       System.out.println(t2 - t1);
       System.out.println(t3 - t2);
       // int_native is consistently ~10x faster
       // total bytecode is smaller for int_native by ~50%, where the addition specific code is ~5x smaller
       // the overhead is caused due to native intergers have to be "shifted" to boxed intergers
   }

   public static void int_native() {
        int i = 0;
        for(int k = 0; k < 100; k++) {
            i++;
        }
   }

   public static void int_boxed() {
        Integer boxed = 0;
        for (int k = 0; k < 100; k++) {
            boxed++;
        }
   }
}
