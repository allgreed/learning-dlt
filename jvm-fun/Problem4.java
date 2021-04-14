public class Problem4 {
   public static void main(String[] args) {
       long t1 = System.nanoTime();
       cmpequals();
       long t2 = System.nanoTime();
       cmpeq();
       long t3 = System.nanoTime();

       System.out.println(t2 - t1);
       System.out.println(t3 - t2);
       // = is consistently ~8x faster
       // bytecode for equals is a few instruction bigger (call overhead)
   }

   public static void cmpeq() {
        String one = "abc";
        String two = "def";
        if (one == two) {
            System.out.println("one == two");
        }
   }

   public static void cmpequals() {
        String one = "abc";
        String two = "def";
        if (one.equals(two)) {
            System.out.println("one.equals(two)");
        }
   }
}
