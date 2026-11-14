package com.geoid.vpn

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * Poliedro facetado (icosaedro) con esfera de nodos, al estilo del prototipo.
 *
 * - Apagado: gira muy despacio, tenue.
 * - Conectado: gira como un planeta (una vuelta cada ~7 s) y brilla en turquesa.
 */
class PolyhedronView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    private val pincel = Paint(Paint.ANTI_ALIAS_FLAG)
    private val pincelVertice = Paint(Paint.ANTI_ALIAS_FLAG)
    private val pincelEstrella = Paint(Paint.ANTI_ALIAS_FLAG)

    var conectado: Boolean = false
        set(valor) {
            field = valor
            invalidate()
        }

    private var angulo = 0f
    private var ultimoMs = 0L

    private val phi = (1.0 + sqrt(5.0)) / 2.0

    // 12 vertices del icosaedro
    private val vertices = listOf(
        doubleArrayOf(-1.0, phi, 0.0), doubleArrayOf(1.0, phi, 0.0),
        doubleArrayOf(-1.0, -phi, 0.0), doubleArrayOf(1.0, -phi, 0.0),
        doubleArrayOf(0.0, -1.0, phi), doubleArrayOf(0.0, 1.0, phi),
        doubleArrayOf(0.0, -1.0, -phi), doubleArrayOf(0.0, 1.0, -phi),
        doubleArrayOf(phi, 0.0, -1.0), doubleArrayOf(phi, 0.0, 1.0),
        doubleArrayOf(-phi, 0.0, -1.0), doubleArrayOf(-phi, 0.0, 1.0)
    )

    // aristas: pares a distancia 2
    private val aristas: List<IntArray> = run {
        val lista = mutableListOf<IntArray>()
        for (i in vertices.indices) {
            for (j in i + 1 until vertices.size) {
                val a = vertices[i]
                val b = vertices[j]
                val d = sqrt(
                    (a[0] - b[0]) * (a[0] - b[0]) +
                        (a[1] - b[1]) * (a[1] - b[1]) +
                        (a[2] - b[2]) * (a[2] - b[2])
                )
                if (kotlin.math.abs(d - 2.0) < 0.01) lista.add(intArrayOf(i, j))
            }
        }
        lista
    }

    // puntos suspensivos para el efecto "esfera de nodos"
    private val nodos: List<DoubleArray> = run {
        val lista = mutableListOf<DoubleArray>()
        for (a in aristas) {
            val p = vertices[a[0]]
            val q = vertices[a[1]]
            for (f in listOf(0.25, 0.5, 0.75)) {
                lista.add(
                    doubleArrayOf(
                        p[0] + (q[0] - p[0]) * f,
                        p[1] + (q[1] - p[1]) * f,
                        p[2] + (q[2] - p[2]) * f
                    )
                )
            }
        }
        lista
    }

    private var estrellas: List<FloatArray> = emptyList()

    init {
        pincel.style = Paint.Style.STROKE
        pincel.strokeWidth = 2.2f
        pincel.strokeCap = Paint.Cap.ROUND

        pincelVertice.style = Paint.Style.FILL

        pincelEstrella.style = Paint.Style.FILL
    }

    override fun onSizeChanged(w: Int, h: Int, ow: Int, oh: Int) {
        super.onSizeChanged(w, h, ow, oh)
        val azar = Random(w * 31 + h)
        estrellas = List(70) {
            floatArrayOf(
                azar.nextFloat() * w,
                azar.nextFloat() * h,
                azar.nextFloat() * 1.6f + 0.6f,
                azar.nextFloat() * 0.55f + 0.15f
            )
        }
    }

    override fun onDraw(canvas: Canvas) {
        val ahora = System.currentTimeMillis()
        if (ultimoMs != 0L) {
            val dt = (ahora - ultimoMs) / 1000f
            // una vuelta cada 7 s conectado; muy lento si no
            val velocidad = if (conectado) 360f / 7f else 6f
            angulo = (angulo + velocidad * dt) % 360f
        }
        ultimoMs = ahora

        val cx = width / 2f
        val cy = height / 2f

        // El poliedro ocupa como maximo ~1.47 veces su radio base al girar, asi
        // que con 0.30 se salia por las esquinas. Con 0.165 entra siempre y deja
        // aire alrededor, sin recortarse en ningun angulo.
        val escala = minOf(width, height) * 0.185f

        // estrellas
        for (e in estrellas) {
            pincelEstrella.color = Color.argb((e[3] * 255).toInt(), 200, 255, 250)
            canvas.drawCircle(e[0], e[1], e[2], pincelEstrella)
        }

        val rad = Math.toRadians(angulo.toDouble())
        val seno = sin(rad)
        val coseno = cos(rad)

        // proyeccion de los puntos
        val proyectados = ArrayList<FloatArray>(vertices.size)
        for (v in vertices) {
            // giro en Y
            val x = v[0] * coseno + v[2] * seno
            val z = -v[0] * seno + v[2] * coseno
            // ligera inclinacion en X
            val y = v[1] * 0.94 - z * 0.10
            val zz = v[1] * 0.10 + z * 0.94

            val factor = 3.2 / (3.2 + zz)
            val sx = cx.toDouble() + x * escala.toDouble() * factor
            val sy = cy.toDouble() + y * escala.toDouble() * factor
            proyectados.add(floatArrayOf(sx.toFloat(), sy.toFloat(), zz.toFloat()))
        }

        // aristas
        for (a in aristas) {
            val p = proyectados[a[0]]
            val q = proyectados[a[1]]
            val prof = ((p[2] + q[2]) / 2f)
            val cerca = (1.6f - prof) / 3.2f
            val alfa = (30 + 190 * cerca.coerceIn(0f, 1f)).toInt()
            pincel.color = if (conectado)
                Color.argb(alfa, 46, 230, 197)
            else
                Color.argb((alfa * 0.55f).toInt(), 60, 140, 140)
            canvas.drawLine(p[0], p[1], q[0], q[1], pincel)
        }

        // nodos de las aristas
        for (n in nodos) {
            val x = n[0] * coseno + n[2] * seno
            val z = -n[0] * seno + n[2] * coseno
            val y = n[1] * 0.94 - z * 0.10
            val zz = n[1] * 0.10 + z * 0.94
            val factor = 3.2 / (3.2 + zz)
            val px = (cx.toDouble() + x * escala.toDouble() * factor).toFloat()
            val py = (cy.toDouble() + y * escala.toDouble() * factor).toFloat()
            val cerca = ((1.6 - zz) / 3.2).coerceIn(0.0, 1.0).toFloat()
            pincelVertice.color = Color.argb(
                (90 + 120 * cerca).toInt(),
                124, 255, 232
            )
            canvas.drawCircle(px, py, 1.6f + 1.4f * cerca, pincelVertice)
        }

        // vertices
        for (p in proyectados) {
            val cerca = ((1.6f - p[2]) / 3.2f).coerceIn(0f, 1f)
            pincelVertice.color = Color.argb(
                (140 + 115 * cerca).toInt(),
                180, 255, 244
            )
            canvas.drawCircle(p[0], p[1], 2.2f + 2.6f * cerca, pincelVertice)
        }

        postInvalidateOnAnimation()
    }
}
