import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.unibe.service.FaceRecognitionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

public class FaceRecognitionServiceTest {

    @InjectMocks
    private FaceRecognitionService faceRecognitionService;

    @Mock
    private DetectionService detectionService;

    @BeforeEach
    public void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testRecognizeFace_Success() {
        // Arrange
        String imagePath = "path/to/image.jpg";
        String expectedPersonId = "12345";
        when(detectionService.processImage(imagePath)).thenReturn(expectedPersonId);

        // Act
        String actualPersonId = faceRecognitionService.recognizeFace(imagePath);

        // Assert
        assertEquals(expectedPersonId, actualPersonId);
        verify(detectionService, times(1)).processImage(imagePath);
    }

    @Test
    public void testRecognizeFace_Failure() {
        // Arrange
        String imagePath = "path/to/image.jpg";
        when(detectionService.processImage(imagePath)).thenReturn(null);

        // Act
        String actualPersonId = faceRecognitionService.recognizeFace(imagePath);

        // Assert
        assertNull(actualPersonId);
        verify(detectionService, times(1)).processImage(imagePath);
    }
}