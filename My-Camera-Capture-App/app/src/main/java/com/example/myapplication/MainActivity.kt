package com.example.myapplication

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.ImageView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import java.nio.ByteBuffer
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import android.view.Surface
import android.widget.TextView

typealias LumaListener = (luma: Double) -> Unit
typealias brighterSideListener = (brighterSide: String) -> Unit

class MainActivity : AppCompatActivity() {

    private var sumDuration: Long = 0
    private var count: Int = 0





    private inner class MyAnalyzer(private val sendMessage: (String) -> Unit, imageView: ImageView) : ImageAnalysis.Analyzer {

        private var previousStartTime: Long = 0
        var blockLateralPosition: String = "none"


        private fun ByteBuffer.toByteArray(): ByteArray {
            rewind()    // Rewind the buffer to zero
            val data = ByteArray(remaining())
            get(data)   // Copy the buffer into a byte array
            return data // Return the byte array
        }

        override fun analyze(image: ImageProxy) {

            val startAnalyzeTime = System.currentTimeMillis()
            //Log.d("Timing", "Current time: $startAnalyzeTime")
            val repDuration = startAnalyzeTime - previousStartTime
//            sumDuration = sumDuration + repDuration
//            count++
            Log.d("Timing", "Rep duration: $repDuration")

            previousStartTime = startAnalyzeTime

            //command
            if (generateImage == true) {
                analyzeAndGenerateImage(image, sendMessage)
            } else {
                analyzeImage(image)
            }
            /*
            val endAnalyzeTime = System.currentTimeMillis()
            val analyzeDuration = endAnalyzeTime - startAnalyzeTime
            Log.d("Timing", "Analyze duration: $analyzeDuration")
            val message = "/Car?move=${command.lowercase()} &$endAnalyzeTime"
            Thread(StringSender(message)).start()
            Log.d("Timing", "endAnalyzeTime: $endAnalyzeTime")
*/
            image.close()
        }

        private fun analyzeAndGenerateImage(image: ImageProxy, sendMessage: (String) -> Unit) {

            if (image.format == PixelFormat.RGBA_8888) {
                val buffer = image.planes[0].buffer
                val width = image.width
                val height = image.height

                var leftCount = 0
                var rightCount = 0

                //var bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)

                val downsampleFactor = 1 // Analyze every other pixel

                //val rgbArray = Array<Array<Int>>(height*width) { arrayOf(0, 0, 0) }
                //var rgbArrayIndex = 1;

                for (y in 0 until height step downsampleFactor) {
                    for (x in 0 until width step downsampleFactor) {
                        // Calculate the position in the buffer (4 bytes per pixel)
                        val position = (y * width + x) * 4

                        val r = buffer.get(position).toInt() and 0xff
                        val g = buffer.get(position + 1).toInt() and 0xff
                        val b = buffer.get(position + 2).toInt() and 0xff


                        val isBluePixel =  (b > 2 * r) && (g > r)

                        if (isBluePixel) { // Adjust this threshold as needed
//                            bitmap.setPixel(x, y, Color.rgb(r, g, b))
                            //bitmap.setPixel(x, y, Color.WHITE)
                            if (y > height / 2) {
                                leftCount++
                            } else {
                                rightCount++
                            }
//                        } else {
//                            bitmap.setPixel(x, y, Color.BLACK)
                        }
                    }
                }

                val counts = "$leftCount | $rightCount"
                blockLateralPosition = when (true) {
                    (leftCount > 100 && rightCount > 100) -> "centre"
                    (leftCount > rightCount) -> "left"
                    (rightCount > leftCount) -> "right"
                    else -> "none"
                }
                sendMessage(blockLateralPosition)

/*
                // Update UI with bitmap
                Handler(Looper.getMainLooper()).post {
                    imageView.setImageBitmap(rotateBitmap(bitmap, 90f))
                }

 */
            }

        }

        private fun rotateBitmap(source: Bitmap, angle: kotlin.Float): Bitmap {
            val matrix = android.graphics.Matrix()
            matrix.postRotate(angle)
            return Bitmap.createBitmap(source, 0, 0, source.width, source.height, matrix, true)

        }

        private fun analyzeImage(image: ImageProxy) {
            if (image.format == PixelFormat.RGBA_8888) {
                val buffer = image.planes[0].buffer
                val width = image.width
                val height = image.height

                var leftCount = 0
                var rightCount = 0

                for (y in 0 until height) {
                    for (x in 0 until width) {
                        // Calculate the position in the buffer (4 bytes per pixel)
                        val position = (y * width + x) * 4

                        val r = buffer.get(position).toInt() and 0xff
                        val g = buffer.get(position + 1).toInt() and 0xff
                        val b = buffer.get(position + 2).toInt() and 0xff

                        // Check if blue is significantly higher than red and green
                        // You can adjust the threshold ratio as needed
                        val redGreenAvg = (r + g) / 2.0
                        val blueRatio = if (redGreenAvg > 0) b / redGreenAvg else 0.0

                        if (blueRatio > 1.5) { // Adjust this threshold as needed
                            if (x < width / 2) {
                                leftCount++
                            } else {
                                rightCount++
                            }
                        }
                    }
                }

                blockLateralPosition = if (leftCount > rightCount) "left" else "right"
            }
        }
    }


    private var imageCapture: ImageCapture? = null

    private lateinit var cameraExecutor: ExecutorService

    private val activityResultLauncher =
        registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        )
        { permissions ->
            // Handle Permission granted/rejected
            var permissionGranted = true
            permissions.entries.forEach {
                if (it.key in REQUIRED_PERMISSIONS && it.value == false)
                    permissionGranted = false
            }
            if (!permissionGranted) {
                Toast.makeText(
                    baseContext,
                    "Permission request denied",
                    Toast.LENGTH_SHORT
                ).show()
            } else {
                startCamera()
            }
        }

    private lateinit var imageView: ImageView
    private var generateImage = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        // Request camera permissions
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            requestPermissions()
        }


        cameraExecutor = Executors.newSingleThreadExecutor()

        imageView = findViewById(R.id.imageView)
        val generatePhotoButton = findViewById<Button>(R.id.generatePhotoButton)
        generatePhotoButton.setOnClickListener { takePhoto() }

    }

    private fun takePhoto() {
        generateImage = true
    }


    private fun startCamera() {

        // for image preview

        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        val viewFinder = findViewById<PreviewView>(R.id.viewFinder) // preview component

        cameraProviderFuture.addListener({
            // Used to bind the lifecycle of cameras to the lifecycle owner
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()

            // Preview
            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(viewFinder.surfaceProvider)
                }


            // for take photo
            imageCapture = ImageCapture.Builder()
                .build()


            val label = findViewById<TextView>(R.id.brighterSideLabel)
            // for image analysis
            val imageAnalyzer = ImageAnalysis.Builder()
                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, MyAnalyzer({ brighterSide ->
                        runOnUiThread {
                            label.text = "Brighter side: $brighterSide"
                            generateImage = true
                        }
                    }, imageView))
                }



            imageAnalyzer.targetRotation = Surface.ROTATION_90
            imageCapture?.targetRotation = Surface.ROTATION_90

            // Select back camera as a default
            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            try {
                // Unbind use cases before rebinding
                cameraProvider.unbindAll()

                // Bind use cases to camera
                cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, imageCapture, imageAnalyzer
                )

            } catch (exc: Exception) {
                Log.e(TAG, "Use case binding failed", exc)
            }

        }, ContextCompat.getMainExecutor(this))

    }


    private fun requestPermissions() {
        activityResultLauncher.launch(REQUIRED_PERMISSIONS)
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(
            baseContext, it
        ) == PackageManager.PERMISSION_GRANTED
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()


    }

    override fun onStop() {
        super.onStop()

        // format used by server
        val message = "/Car?move=" + "s "

        if (count != 0) {
            Log.d("Timing", "Average duration: ${sumDuration / count}")
        }
    }

    override fun onPause() {
        super.onPause()

        // format used by server
        val message = "/Car?move=" + "s "

        // TODO format message for Web_control_car.py
        Thread(StringSender(message)).start()  // Send to ESP
    }

    companion object {
        private const val TAG = "CameraXApp"
        private const val FILENAME_FORMAT = "yyyy-MM-dd-HH-mm-ss-SSS"
        private val REQUIRED_PERMISSIONS =
            mutableListOf(
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO
            ).apply {
                if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
                    add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                }
            }.toTypedArray()
    }

    fun sendMessage(command: String) {

        // Get current timestamp (milliseconds since Unix epoch)
        val timestamp = System.currentTimeMillis()

        val message = "/Car?move=${command.lowercase(Locale.getDefault())} &$timestamp"

        Thread(StringSender(message)).start()
    }


}