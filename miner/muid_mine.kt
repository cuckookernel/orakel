import java.security.MessageDigest
import java.io.File
import java.net.URL
import java.security.InvalidParameterException

@kotlin.ExperimentalUnsignedTypes
const val B16 : UByte = 16u
@kotlin.ExperimentalUnsignedTypes
const val B48 : UByte = 48u
@kotlin.ExperimentalUnsignedTypes
const val B87 : UByte = 87u
@kotlin.ExperimentalUnsignedTypes
const val B10 : UByte = 10u

fun ByteArray.toInts() = this.map { it.toInt() }

@kotlin.ExperimentalUnsignedTypes
fun main() {
        val animDb = AnimalsDb()
        println("bloom has ${animDb.bloom.count()}")

        // val p1 = Pair(hexStringToByteArray("3E17AB1ED090"), 11)
        // println( "${p1.first.hex()} ${p1.first.toInts() } ${p1.second} => ${animDb.bytesLens.contains(p1)}" )
        // println( "pos = ${animDb.byteLensList.binarySearch( p1, animDb.cmp ) }}")
        //animDb.bytesLens.take(10).forEach { (ba, len) -> println( "${ba.hex()}, $len") }

        // println("animalHashes has ${animalHashes.size} (min: ${animalHashes.min()}, max: ${animalHashes.max()}} )" +
        //        "animalsSetOfByteArr has ${animalsSetOfByteArr.size}")

        // val animalHashes1 = animalsSetOfByteArr.map { it.hashCode() }.toSet()
        // println("animalHashes has ${animalHashes1.size} (min: ${animalHashes1.min()}, max: ${animalHashes1.max()}} )" +
        //        "animalsSetOfByteArr has ${animalsSetOfByteArr.size}")

        val md = MessageDigest.getInstance("SHA-256")

        // val key = "71d157b442b1b40582000000177a7b64".toByteArray()
        // md.update(key)
        // val sha256_0 = md.digest()
        // val len0 = animDb.checkHash( sha256_0 )
        // val bloom_key = hash( sha256_0, 11)
        // println( "key = ${key.str()} hash=${sha256_0.hex()}\ninbloom=${animDb.bloom.contains(bloom_key)} len = $len0")
        // animDb.checkHash(sha256_0)
        // checkHash(animDb.animalsSet, sha256_0)

        // val seed = byteArrayOf(45, 64, 12, 13, 0, 0, 0, 0, 0, 0, 0, 0);
        // val seed_b = "71d157b442b1b405839dd98d0e149572".toByteArray()
        val seed_b = "7e1707b442b1b405839dd98d0e149572".toByteArray()
        // val seed = ( intArrayOf(113, 209, 87, 180, 66, 177, 180, 5, 130, 157, 217, 141, 14, 20, 149, 114)
        //             .map{ it.toByte() }.toByteArray() )

        println( "key0 = ${seed_b.str()} len(seed) = ${seed_b.size} ")
        md.update(seed_b)
        val sha256_0 = md.digest()
        println( "hash0 = ${sha256_0.hex()}")
        val len_0 = animDb.checkHash( sha256_0 )
        if( len_0 > 0 ) {
            println("key=${seed_b.str()} hash=${sha256_0.hex()} len=${len_0}")
        }
        val seed_u = seed_b.toUByteArray()

        val myFile = File( "muids_${System.currentTimeMillis()}.txt" )
        val start_tm = System.nanoTime()

        myFile.printWriter().use { out ->
            var a = 0UL;
            while( true ) {
                set_last_bytes(seed_u, a)
                // println( seed_u.str()  )
                md.reset()
                md.update(seed_u.toByteArray())
                val sha256 = md.digest()
                val len = animDb.checkHash(sha256)
                if (len > 8) {
                    out.println("a=$a key=${seed_u.str()} hash=${sha256.hex()} len=${len}")
                    out.flush()
                    if( len > 11) {
                        println("a=$a key=${seed_u.str()} hash=${sha256.hex()} len=${len}")
                    }
                    val url = "http://localhost:8000/keys/save/${seed_u.str()}"
                    println( URL(url).readText() )
                }
                if (a % (1_000_000u) == 0UL) {
                    val elapsed = (System.nanoTime() - start_tm) / 1e9
                    println("${a.toDouble() / 1e9} : ${String.format("%.2f", elapsed)} secs ")
                }
                a += 1UL
            }
        }
}


@kotlin.ExperimentalUnsignedTypes
class AnimalsDb {
    // val animalsSet = readAnimals()
    val bytesLens = readAnimals().toSetOfByteArray()

    // val animalsBAstrs = animalsSetOfByteArr.map { Tuple( it.first.hex(), it.first, it.second ) }.sortedBy{ it.first }
    // 3E17AB1ED090

    val cmp = Comparator<Pair<ByteArray, Int>> { (a, la), (b, lb) ->
        var cmp = la.compareTo(lb)
        if (cmp == 0) {
            for (i in a.indices) {
                cmp = a[i].compareTo(b[i])
                if (cmp != 0) break
            }
        }
        cmp
    }

    val byteLensList = bytesLens.toList().sortedWith( cmp )

    val bloom = {
        val bloom0 = BloomFilter(nbits = (1 shl 20))
        bytesLens.forEach {
            val key = hash(it.first)
            bloom0.set( key )
        }
        bloom0
    }()

    fun checkHash( sha256: ByteArray ): Int {

        for ( len in 6 .. 15 ) {
            val key = hash( sha256, len )
            if ( bloom.contains(key) ) {
                val hexStr = sha256.copyOfRange(0, (len + 1) / 2)

                if( len % 2 == 1 ) {
                    val b = sha256[len / 2]
                    hexStr[len / 2] = b.toInt().and( first4 ).toByte()
                }

                val pos = byteLensList.binarySearch( Pair( hexStr, len ), comparator=cmp )
                // println("len: $len ${hexStr.hex()} ")
                if( pos >= 0 ) {
                    // val elem = byteLensList[pos]
                    // println( "is animal! ${elem.first.hex()} len1=${elem.second} len=$len")
                    return len
                }
            }
        }
        return 0
    }

}


/*
fun main2( animals: Set<Pair<ByteArray, Int>> ) {
    // val animalHashes = animals.map { hash(it.first) }.toSet()
    val animalsByHash = HashMap<Int, ArrayList<ByteArray>>()
    animals.forEach {
        val key = hash(it.first)
        if (animalsByHash.containsKey(key)) {
            animalsByHash[key]!!.add(it.first)
        } else {
            animalsByHash[key] = arrayListOf(it.first)
        }
    }

} */


@kotlin.ExperimentalUnsignedTypes
class BloomFilter(val nbits: Int)  {
    private val bytes: ByteArray = ByteArray(nbits / 8) {0}

    fun set(bi : Int) {
        val bi1 = if (bi < 0) (0xFFFFFFFF + bi).toInt() else bi
        assert( bi1 >= 0)  {"bi=$bi bi1=$bi1"}
        val i0 = bi1 % nbits
        val rem = i0 % 8
        val i = i0 / 8
        assert( i >= 0)  {"i=$i i0=$i0"}

        bytes[i] = ( bytes[i].toInt() or (1 shl rem) ).toByte()
    }

    fun contains( bi: Int ): Boolean {
        val bi1 = if (bi < 0) (0xFFFFFFFF + bi).toInt() else bi
        assert( bi1 >= 0)  { "bi=$bi bi1=$bi1"}
        val i0 = bi1 % nbits
        val rem = i0 % 8
        val i = i0 / 8
        return bytes[i].toInt() and (1 shl rem) != 0
    }

    fun count() : Int {
        var cnt = 0
        for( b in bytes ){
            for( i in 0 until 8 ) {
                cnt += if( (b.toInt() and (1 shl i)) != 0 ) { 1 } else { 0 }
            }
        }
        return cnt
    }
}

/*
fun checkHash( animalsSet: Set<String>, sha256: ByteArray ): Int {
    val hexStr = sha256.hex()

    for ( len in 6 .. 15 ) {
        val subStr = hexStr.substring(0, len)
        if( animalsSet.contains( subStr ) ) {
            print( "checkHash0: $subStr is animal len:$len")
            return len
        }
    }
    return 0
}*/


/*
fun tmp( sha256: ByteArray, tmp: ByteArray, len: Int, animals: Set<Pair<ByteArray, Int>>): Int {
    val sha = sha256.copyInto( tmp, endIndex=tmp.size )
    if( len % 2 == 1 ) {
        val b = sha[len/2]
        tmp[len / 2] = b.toInt().and( first4 ).toByte()
    }
    val b_len = (len + 1) / 2
    if( animals.contains( Pair(tmp.copyOfRange(0, b_len), len) ) ) {
        return len
    }
    return 0
}*/


fun readAnimals(): Set<String> {
    val aniList = File("animals.txt").bufferedReader().readLines()
    return aniList.map { it.trim().toUpperCase() }.toSet()
}

fun Set<String>.toSetOfByteArray(): Set<Pair<ByteArray, Int>> = this.map {
    Pair( hexStringToByteArray(it), it.length ) }.toSet()

fun hexStringToByteArray( a_str: String ): ByteArray  {
    val hex_lc = a_str.toLowerCase()

    val ret: ByteArray = (hex_lc.indices step 2 ).map { idx ->
        val d1 = hex_lc[idx].hexval()
        val d2 = if(idx + 1 < hex_lc.length) hex_lc[idx+1].hexval() else 0
        ((d1 shl 4) + d2).toByte()
    }.toByteArray()

    return ret
}

fun Char.hexval(): Int = if (( this >= '0') && ( this <= '9')) {
    this - '0'
} else if ((this >='a') && (this <='f')) {
    this - 'a' + 10
} else {
    throw InvalidParameterException()
}

fun ByteArray.hex( ): String = this.joinToString("") { String.format("%02X", it) }

fun ByteArray.str() : String = this.joinToString("") { it.toChar().toString()}

@kotlin.ExperimentalUnsignedTypes
fun UByteArray.str() : String = this.joinToString("") { it.toByte().toChar().toString()}


@kotlin.ExperimentalUnsignedTypes
fun set_last_bytes( seed: UByteArray, a : ULong ) {
    var a1 = a
    val n = seed.size
    for( i in 1 until 9 ) {
        val b = a1.toUByte()
        if ( b == 0.toUByte() ) {
            seed[n - 2 * i + 1] = B48
            seed[n - 2 * i ] = B48
            continue
        }
        val d1 = (b % B16).toUByte()
        val d2 = (b / B16).toUByte()
        // println( "$b $d1, $d2" )
        seed[n - 2 * i + 1] = ( if (d1 < B10) { B48 + d1 } else { B87 + d1 } ).toUByte()
        seed[n - 2 * i ] =  ( if (d2 < B10)  { B48 + d2 } else { B87 + d2 } ).toUByte()
        a1 = (a1 - b) shr 8
    }
}

/*
fun example( md: MessageDigest ) {
    md.update("71d157b442b1b405829dd98d0e149572".toByteArray() )
    val digest = md.digest()
    println("hello " + String.format("%02X", digest[0]) + " " +  digest.size.toString() )

    md.update("71d157b442b1b405829dd98d0e149572".toByteArray() )
    val digest2 = md.digest()
    println("hello " + String.format("%02X", digest2[0]) + " " +  digest.size.toString() )
}*/

const val mprime = 1L shl 61
const val first4 = 0xf0

fun hash( ba: ByteArray, len: Int = 2 * ba.size ) : Int {
    // len is number of hexadecimal digits
    var ret = 0L
    var tmp = 0L

    val odd = len % 2 == 1
    val b_len = len / 2 + if(odd) { 1 } else { 0 }

    for ( i in 0 until b_len ) {
        val byte = if ( (i + 1 == b_len) && odd ) {
            (ba[i].toInt() and first4).toByte()
        } else {
            ba[i]
        }

        tmp += byte.toInt() shl ((i % 4) * 8)
        // println( "i: $i byte=$byte tmp1=$tmp")

        if( (i % 4 == 3) || (i+1 == b_len) ) {
            tmp *= 1231312312321321313L
            tmp += 7612123123213212213L
            tmp %= mprime
            ret += tmp
            // println( "tmp=$tmp" )
            tmp = 0
        }
    }

    // println("ret=$ret")
    return ret.toInt().and(0x7FFFFFFF.toInt())  // remove minus sign
}