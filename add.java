import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.fail;

public class ParallelTest {

    private static final String CLASSPATH_KARATE_FEATURES = "classpath:karate";

    @Test
    void testAllParallel() throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(2);
        ExecutorService executor = Executors.newFixedThreadPool(2);

        executor.submit(() -> {
            try {
                Results sseResponse = Runner.path(CLASSPATH_KARATE_FEATURES)
                        .parallel(1)
                        .reportDir("target/surefire-reports") // Specify report directory
                        .run();
                log("SSE Response:", sseResponse);
                latch.countDown();
            } catch (Exception e) {
                fail("First test failed: " + e.getMessage());
            }
        });

        executor.submit(() -> {
            try {
                Results approveResponse = Runner.path(CLASSPATH_KARATE_FEATURES)
                        .parallel(1)
                        .reportDir("target/surefire-reports") // Use the same report directory
                        .run();
                log("Approve Response:", approveResponse);
                latch.countDown();
            } catch (Exception e) {
                fail("Second test failed: " + e.getMessage());
            }
        });

        latch.await(60, TimeUnit.SECONDS);
        executor.shutdownNow();
    }

    // ... (rest of the code remains the same)
}
