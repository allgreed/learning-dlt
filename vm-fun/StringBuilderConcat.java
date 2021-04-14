public class StringBuilderConcat {
    public void StringConcatTest() {
        String s = "First ";
        s += " Second";
        s += " Third";
        System.out.println(s);
    }

    public void StringBuilderTest() {
        StringBuilder sb = new StringBuilder("First ");
        sb.append(" Second");
        sb.append(" Third");
        System.out.println(sb.toString());
    }
}
