package com.example.myapplication

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
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
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import android.view.Surface
import android.widget.TextView
import kotlin.math.abs

class MainActivity : AppCompatActivity() {


    private inner class MyAnalyzer(private val sendMessage: (String) -> Unit) : ImageAnalysis.Analyzer {

        private var previousStartTime: Long = 0
        var command: Char = 's'


        private fun ByteBuffer.toByteArray(): ByteArray {
            rewind()    // Rewind the buffer to zero
            val data = ByteArray(remaining())
            get(data)   // Copy the buffer into a byte array
            return data // Return the byte array
        }

        override fun analyze(image: ImageProxy) {

            //val startAnalyzeTime = System.currentTimeMillis()
            //Log.d("Timing", "Current time: $startAnalyzeTime")
            //val repDuration = startAnalyzeTime - previousStartTime
            //Log.d("Timing", "Rep duration: $repDuration")
            //previousStartTime = startAnalyzeTime

            //command
            val buffer = image.planes[0].buffer
            val width = image.width
            val height = image.height

            val downsampleFactor = 1 // Option to increase analysis speed at cost of accuracy

            var totalMass = 0
            var weightedSumX = 0

            for (row in 0 until height step downsampleFactor) {
                for (col in 0 until width step downsampleFactor) {
                    // Calculate the position in the buffer (4 bytes per pixel)
                    val position = (row * width + col) * 4

                    val r = buffer.get(position).toInt() and 0xff
                    val g = buffer.get(position + 1).toInt() and 0xff
                    val b = buffer.get(position + 2).toInt() and 0xff

                    val isBluePixel =  (b > 2 * r) && (g > r)
                    if (isBluePixel) { // Adjust this threshold as needed
                        totalMass++
                        val x = -(row - height/2)
                        weightedSumX += x
                    }
                }
            }

            val comX = if (totalMass > 0) weightedSumX / totalMass else -1

            val prevCommand = command
            command = when (true) {
                (totalMass < 40) -> 'd' // Block is not in frame
                (abs(comX) < 20) -> 'f' // Block within setpoint bound
                (abs(comX) < 555 && prevCommand != 's') -> 's'  // Block moves past stop point. Makes command alternate between l and r
                (comX < 0) -> 'l'   // Block is in the left half of the image
                (comX > 0) -> 'r'   // Block is in the right half of the image
                else -> 's'
            }
            sendMessage("$comX $command $totalMass")

            //val endAnalyzeTime = System.currentTimeMillis()
            //Log.d("Timing", "endAnalyzeTime: $endAnalyzeTime")
            //val analyzeDuration = endAnalyzeTime - startAnalyzeTime
            //Log.d("Timing", "Analyze duration: $analyzeDuration")
            //Log.d("command", "$prevCommand to $command")

            if (command != prevCommand) {
                Log.d("command", "sending $command")
                Thread(CharSender(command)).start()
            }
            Log.d("cmd", "$prevCommand -> $command")
            image.close()
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
    }


    private fun startCamera() {

        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        val viewFinder = findViewById<PreviewView>(R.id.viewFinder) // preview GUI component

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
                    it.setAnalyzer(cameraExecutor, MyAnalyzer({ counts ->
                        runOnUiThread {
                            label.text = counts
                            generateImage = true
                        }
                    }))
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
        Thread(CharSender('s')).start()  // Send to ESP

    }

    override fun onStop() {
        super.onStop()
        Thread(CharSender('s')).start()  // Send to ESP
    }

    override fun onPause() {
        super.onPause()
        Thread(CharSender('s')).start()  // Send to ESP
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


}