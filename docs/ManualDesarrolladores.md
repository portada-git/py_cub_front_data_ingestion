<div align="center">
<h1>Configuración para la extracción de datos</h1>
<h2>Manual para desarrolladores: Extracción de información de noticias en el contexto del proyecto portada</h2>
</div>

# Últimas novedades
Se ha añadido un _parser_ que trabaja contra openAI para realizar la extracción de datos a partir de un texto. Este _parser_ se integra en el sistema de configuración general de los extractores y permite usarlo en cualquier nivel del texto analizado, de manera que puede usar directamente el texto de los ficheros, o alguno de los campos ya extraídos mediante otro extractor (se puede encontrar más información detallada en [Configuración de un analizador de tipo _openai_](#configuraci%C3%B3n-de-un--analizador-de-tipo-openai).  También se ha añadido un nuevo calculador para poder crear funciones externas al programa, vía llamada a un microservicio. El nuevo calculador recibe los datos de conexión del microservicio, así como los parámetros esperados durante la ejecución. Esto va a permitir expandir los calculadores sin necesidad de integrarlos en el programa. Encontraréis la información detallada al final de la sección [Calculadores existentes](#calculadores-existentes).


# Manual para desarrolladores

Este manual se ha creado básicamente para ayudar a los desarrolladores del proyecto **_PortADa_** a crear los archivos de configuración necesarios para que las aplicaciones PAPI y PAPCLI puedan extraer los datos referentes a las embarcaciones llegadas a los diferentes puertos de estudio referenciadas en los periódicos utilizados como fuentes en el contexto del proyecto portada. 

Para facilitar la configuración de los extractores, se ha desarrollado una aplicación no integrada en PAPICLI de uso exclusivo para desarrolladores. Se puede conseguir en el enlace [autoNewsExtractorDev.zip](https://drive.google.com/file/d/1UBCOwoWMHVPY9bpfrQbXnQQh5WSmgjz4/view?usp=sharing). Dicho enlace solo contiene los ejecutables y scripts para preparar la extracción, por lo que será necesario añadir los directorios de configuración.  El código de dicha aplicación se encuentra en el siguiente repositorio de Github: *[jportada_boat_fact_extractor](https://github.com/portada-git/jportada_boat_fact_extractor)*. 

Antes de entrar en detalle sobre la cuestión práctica de la configuración de los extractores, se dará una explicación de la biblioteca en la que se ha basado la aplicación de extracción. Se trata de *[jportada_auto_news_extractor_lib](https://github.com/portada-git/jportada_auto_news_extractor_lib)*.

# La Biblioteca _jportada_auto_news_extractor_lib_

La biblioteca *[jportada_auto_news_extractor_lib](https://github.com/portada-git/jportada_auto_news_extractor_lib)*, es una biblioteca genérica para facilitar la creación de utilidades orientadas a la extracción de datos de fuentes textuales. Presenta una gran flexibilidad, lo que supone minimizar la creación de nuevo código. A continuación presentamos 3 funcionalidades que serán útiles para realizar la extracción en el contexto del proyecto portada.

## Funcionalidades de *jportada_auto_news_extractor_lib*
### Ensamblador de archivos digitales

Esta funcionalidad permite unir, en un solo archivo, los múltiples textos pertenecientes a una misma unidad informativa, que el procesador OCR haya generado a partir de los periódicos digitalizados. Aunque la biblioteca permitiría usar otras metodologías, en el proyecto **_PortAda_** se decidió usar el enfoque basado en el nombre de los archivos generados por el procesador OCR. Durante el proceso de obtención del texto a partir de las imágenes de los periódicos analizados, las imágenes se fraccionan en bloques para facilitar su ordenación y transcripción textual. En el proyecto se ha optado por nombrar cada bloque con un nombre que permita identificar la fecha, el nombre del periódico, la edición del ejemplar (mañana, tarde, ...), así como el tipo de noticia, la página y el número de bloque procesado por el OCR. 

Este formato nos permite determinar que todos los archivos de texto pertenecientes a una misma fecha, periódico, y edición, pueden contener información relacionada de una misma unidad de información y, por tanto, necesitamos unirla en un solo texto para poder disponer de un texto bien ordenado. 

Además, al tiempo que se realiza la unión, se consigue obtener información extra que no se encuentra en la noticia, objeto de nuestro análisis y posterior extracción. No referimos a los datos indicados en el nombre: Fecha del ejemplar, lugar de edición, nombre del periódico, edición del ejemplar y páginas de las que se realizará la extracción. Dicha información será incorporada, al resto de datos extraídos. 

Por ello, es importante que los nombres de los archivos sigan el patrón descrito `AAAA_MM_DD_PUE_NP_E_PG_BLOC.txt`, donde:
  - AAAA corresponde al año de edición,
  - MM al mes y
  - DD al día.
  - PUE indica el nombre del puerto al que hace referencia la noticia (BCN, BUE, HAB, MAR).
  - NP se refiere al nombre del periódico (DB por diario de Barcelona, DM por diario de la marina, EN por el nacional, LP por la prensa, SM por le semafore de Marseille, ...).
  - E indica la edición del ejemplar (M por mañana, T por tarde, N por noche o U por única).
  - PG contendrán el número de página, con dos dígitos de manera obligatoria,
  - Los últimos 4 dígitos (BLOC) indicarán el número del bloque del que se ha transcrito el texto.

Por ejemplo, el archivo 1854_04_25_BUE_EN_U_E_08_0005.txt indicaría que se trata del quinto bloque de la página 8 de las noticias referidas a las entradas de buques al puerto de Buenos Aires del periódico _El Nacional_ de la única edición del día 25 de abril de 1854.

### Cortador de los fragmentos objetivo 

Una vez unidos todos los bloques en uno solo, esta función extrae el fragmento o la sección de noticias de destino para su análisis, separándolo del contenido no relacionado. En el proyecto PortAda, esto se logra utilizando expresiones regulares para definir los puntos de inicio y fin de la sección relevante. Este paso garantiza que solo se procese el texto requerido, lo que reduce el ruido que podría introducir errores durante la extracción de datos.

### Analizador para extraer la información

La última de las funcionalidades tiene como objetivo extraer los datos contenidos en el texto de las noticias, clasificándolo en categorías predefinidas a las que llamaremos campos. Estos son:

 - __model_version__: Indica la versión del nombre del campo model.
 - __parsed_text__: Es es fragmento de texto correspondiente a un única entrada des de el cual se ha realizado la extración de los datos.
 - __publication_date__: Muestra la fecha del periódico
 - __publication_name__: Muestra el nombre del periódico en su version reducida: DB pa el Diario de Barcelona, DM para el diario de la Marina, LP para La Prensa de Buenos Aires o SM para Le Semaphore de Marsella, ...
 - __publication_edition__: Indica la edición del periódico en caso de que haya más de una al día: M para mañana, T para tarde o N para noche. En caso de que haya una sola edición el valor será U (única).
 - __news_section__: Es el tipo de noticia que se analiza. Puede tomar valores como E para entradas de buques o M para manifiestos de descarga.
 - __travel_departure_port__: Indica el puerto de salida del buque en este viaje
 - __travel_arrival_port__: Indica el puerto de llegada (Marsella, Buenos Aires, La Habana o Barcelona) del buque en este viaje. En la mayoría de los casos, esta información no aparece en las noticias y se deduce implícitamente según el periódico
 - __travel_departure_date__: Indica la fecha de salida del barco del puerto de salida
 - __travel_arrival_date__: Indica la fecha en la que el barco llegó al puerto de llegada (Marsella, Buenos Aires, La Habana o Barcelona)
 - __travel_arrival_moment__: Indica la hora de llegada al puerto. Puede expresarse como hora de llegada o como un periodo más amplio (mañana, tarde, noche, ...)
 - __travel_duration_value__: Indica el tiempo que el barco estuvo viajando desde el puerto de salida al puerto de llegada días u horas
 - __travel_duration_unit__: Indica la unidad de tiempo en la que se expresa la duración.
 - __travel_port_of_call_list__: Indica la lista de puertos (y opcionalmente más información como fechas de llegada o salida) en los que el barco había hecho escala durante su trayecto al puerto de llegada. Si la información de esta lista es solo el nombre de los puertos, la lista estará compuesta por nombres de puertos separados por comas. En caso contrario, cada información de escala se encerrará entre paréntesis cuadrados separados, también por comas, y dentro de cada uno de ellos se especificaran si fuera posible: el nombre del puerto, la fecha de llegada a ese puerto y la fecha de salida (de acuerdo a los 3 campos siguientes). 
 - __port_of_call_place__: Muestra el nombre del puerto de un elemento de la lista de puertos de escala
 - __port_of_call_arrival_date__: Muestra la fecha de llegada de un elemento de la lista de puertos de escala
 - __port_of_call_departure_date__: Muestra la fecha de salida de un elemento de la lista de puertos de escala
 - __ship_type__: Describe el tipo de barco (bergantín, goleta,  vapor, etc.) que menciona el periódico
 - __ship_flag__: Hace referencia al nombre del país o región de la bandera del barco descrito por el periódico
 - __ship_name__: Indica el nombre del barco que normalmente se presenta completo, como se menciona en la fuente del periódico
 - __ship_tons_capacity__: Especifica la capacidad del barco en toneladas presentada como un valor numérico con la unidad de medida. En el caso de los barcos, esto siempre es lo mismo, ya que se refiere al tonelaje del buque. Este dato se da normalmente con abreviaturas como "ton." o "t."
 - __ship_tons_unit__: Referred to the unit of the ship's tonnage. Usually given with abbreviations such as "ton." or "t."
 - __master_role__: Hace referencia a la categoría de la persona que comanda el buque. Puede ser capitán o patrón, aunque en algunos casos también aparece piloto. Las abreviaturas que se utilizan para designarlos suelen ser “c” y “p”, respectivamente
 - __master_name__: Es la identificación nominal de la persona que comanda el buque. Puede aparecer de varias formas, al menos lleva el apellido, precedido de su cargo (rol). Indica el apellido del capitán del buque, a menudo precedido de “cap.” o “c.”
 - __ship_agent_name__: Esta información puede indicar tanto el agente del buque, es decir, la persona que se encarga de las transacciones y la operación del buque, como el armador, es decir, la persona que es propietaria del buque o de parte del mismo. En ocasiones también puede hacer referencia al armador
 - __crew_number__: Es el valor numérico de la tripulación del buque.
 - __cargo_list__: Es la descripción de la lista con la información relativa a toda la carga transportada por el buque entrante (tipo de carga, cantidad, persona receptora de la carga, si la hay o “a la orden” en caso contrario, etc.). Inicialmente, se mostrará como descripción textual separada por comas, pero en una segunda fase, cada mercancía se descompondrá en los 6 siguientes campos.
 - __cargo_merchant_name__: Es la persona a la que iba destinada la carga, muchas veces será el comerciante que la había comprado y que se hizo cargo de ella en el momento de la descarga. Indica el destinatario de la carga, con ocasional mención a “divers” [varios/diversos].
En este caso vemos nombres de personas o empresas. Estos nombres tienen las mismas características y dificultades que el resto de denominaciones. En ocasiones los barcos llegaban a carga completa y estaban destinados a la misma persona, y en otros casos, cada carga tenía su destinatario. También aparece con frecuencia la expresión “a la orden”, que en principio es una carga para ser vendida a su llegada a puerto y que, por el contrario, no tiene un propietario anterior, más allá del propio capitán personalmente o por cuenta de alguien.
 - __cargo_commodity__: Expresa los productos o tipos de mercancías que han llegado. Es un valor muy variable, las mercancías más habituales son el carbón o el algodón, pero existe una extraordinaria diversidad de productos que llegan al puerto.
 - __cargo_quantity__: Expresión numérica del importe de la carga
 - __cargo_unit__: Expresa las unidades en las que aparece la carga. Estas pueden ser unidades de peso, volumen, recuentos o unidades relativas al embalaje.
 - __cargo_port_origin__: Puerto de origen de la carga
 - __cargo_port_destination__: Puerto de destino de la carga
 - __quarantine__: Información relativa a condiciones especiales de la llegada motivadas por circunstancias sanitarias.
 - __forced_arrival__: Indicación sobre las causas de la llegada forzosa
 - __ship_amount__: Este campo aparece únicamente en modelos cuantitativos donde, en lugar de especificar la información de cada buque, se indica el número de buques que han llegado o están a punto de llegar. Normalmente, se trata de un modelo específicamente pensado para el transporte de cabotaje.
 - __ship_origin_area__: Este campo aparece únicamente en modelos cuantitativos donde, en lugar de especificar la información de cada buque, se utiliza la zona de origen o de transporte. Normalmente, se trata de un modelo específicamente destinado al transporte de cabotaje.
- __info_ship_type__: [TO DO]
- __info_ship_name__: [TO DO]
- __info_master_role__: [TO DO]
- __info_master_name__: [TO DO]
- __info_meeting_place__: [TO DO]
- __info_meeting_date__: [TO DO]
- __info_port_deparure__: [TO DO]
- __cargo_info_departure_date__: [TO DO]
- __info_port_destination__: [TO DO]
- __info_behind__: [TO DO]

Hay dos enfoques metodológicos disponibles para la extracción:
1. **Basado en expresiones regulares**: se basa en expresiones regulares y tiene componentes definidos en la biblioteca.
2. **Basado en IA**: utiliza IA generativa (OpenAI) para la extracción de datos.

## Diseño de software basado en proxies
La biblioteca *[jportada_auto_news_extractor_lib](https://github.com/portada-git/jportada_auto_news_extractor_lib)* se ha diseñado para permitir diversos enfoques metodológicos en el tratamiento de la extracción. A fin de facilitar el desarrollo de los enfoques actuales y permitir futuras alternativas, la biblioteca dispone de un conjunto de proxies capaces de manejar, de forma transparente, múltiples enfoques que respondan a una funcionalidad determinada, organizada alrededor de una interfaz.

![diagrama UML del patron proxy](media/proxy_annotation_system.jpg)

Se ha implementado 4 patrones diferentes de tipo proxy. Uno para cada funcionalidad (ensamblaje de archivos, segregación de fragmentos-objetivo y analizador de contenido) y un cuarto sistema para gestionar los llamados calculadores de campos. Al iniciarse la ejecución, cada proxy busca entre un conjunto definido de  paquetes, las classes anotadas por la anotación de marcaje asociada al proxy. Al iniciarse la ejecución, el proxy usará su anotación asociada para  encontrar todas las classes que implementen la interficie vinculada al proxy y así gestionar la delegación de las peticiones de los clientes en función de un parámetro de selección (el enfoque).

### Sistema del proxy para la funcionalidad de ensamblaje de archivos
En este caso solo se ha implementado un único enfoque específico para el proyecto PortAda, aunque en un futuro podrían implementarse otros. El patrón está basado en un _Proxy_ anotado por _InformationUnitBuilderMarkerAnnotation_ que implementa la interfaz _InformationUnitBuilder_ por delegación sobre la clase _InformationUnitBuilderFromSdlFiles_ (ver diagrama).

![diagrama UML del sistema InformationBuilder](media/InformationUnitBuilderSystem.jpg)

### Sistema del proxy para la funcionalidad de segregación de fragmentos-objetivo
De forma similar a la anterior, este sistema dispone de un Proxy anotado por _TargetFragmentCutterMarkerAnnotation_, implementa la interfaz _TargetFragmentCutter_ y delega en las classes _TargetFragmentCutterByRegex_ y _TargetFragmentCutterByOpenAI_tal como se muestra en el siguiente diagrama:

![diagrama UML del sistema TargetFragmentCutter](media/TargetFragmentCutterSystem.jpg)

### Sistema del proxy para la funcionalidad de analizador de contenido para la extracción de datos
En este caso, el sistema dispone de un Proxy anotado por _ProxyAutoNewsExtractorParser_, implementa la interfaz _ExtractorParser_ y delega en las classes _RegexExtractorParser_ y _OpenAiExtractorParser_ tal como se muestra a continuación:

![diagrama UML del sistema ExtractorParser](media/ContentParserForExtracting.jpg)

### Sistema del proxy para las utilidades FieldCalculator

Las utilidades FieldCalculator están diseñadas para facilitar la manipulación y cálculo de campos extraídos o no,  a partir de un conjunto de datos llegados a través de la configuración y los  parámetros durante la ejecución del cálculo. El diagrama UML ayuda a entender el diseño:

![diagrama UML del sistema DataExtractorCalculator](media/ExtractorCalculator.jpg)

A fin de facilitar todas las posibles inicializaciones de modo automatizado, estas, se vinculan a una clase _Enum_ la cual contiene el identificador para cada uno de los argumentos usados en una inicialización. Actualmente, es posible inicializar con los siguientes datos:

 1. *config*. En este caso el calculador se inicializa con un objeto de tipo *Configuration*. En el caso del proyecto PorTAda un objeto de tipo *AutoNewsExtractorConfiguration* con todos los parámetros necesarios para gestionar la extracción de las noticias de *barcos entrados a puerto*.  Desde el calculador, se accede al objeto *Configuration* de la inicialización, mediante el método *getInitData("config")*.
 2. *parserId*. Este argumento de inicialización es de tipo *Integer*, e indica cuál de los múltiples analizadores de contenido para la extracción se está usando en este momento. A menudo la extracción pude contener diversos patrones diferentes dentro de una misma sección o noticia. Por ello se pueden usar diferentes analizadores en cada proceso de extracción. Estos se definen en la configuración (*AutoNewsExtractorConfiguration*) mediante una lista de candidatos. El valor *parserId* indica cuál de ellos se encuentra activo en el momento de procesar este cálculo.  Desde el calculador, se accede al valor entero pasado durante la inicialización, mediante el método *getInitData("parserId")*.
 3. *constants*. Esta opción permite inicializar el calculador con un conjunto de valores constantes en formato de objeto JSON. Se accede al objeto JSON con los valores de las constantes accediendo al método *getInitData("constants")*.
 4. *extracted_data*. Esta opción solo debería usarse en casos muy específicos. De hecho, los valores de los datos extraídos se pasan, ya sean los actuales o los previos, se pasan a través de parámetros en la llamada al método *calculate* pues ello permite pasar solo el valor y evitar manipulaciones en los datos extraídos. Sin embargo, cuando un objeto calculador deba realizar varias manipulaciones en diferentes campos, resulta útil pasar los datos extraídos (se inicializan pasándolos por referencia) para poder realizar todos los cambios con un solo calculador en lugar de tener que implementar un calculador para cada campo a cambiar. 

El método calculate, puede recibir un parámetro con un objeto, a lista que contenga todos los datos necesarios. Por ejemplo, el calculador llamado *ReplaceIdemByValueCalculator* recibe un array de cadenas de caracteres con dos posiciones, en la primera se enviará el valor actual del campo que se desea manipular en caso de que contenga la palabra* idem* o equivalente. Puesto que ello significa que el valor de eses campo, en realidad hace referencia al último valor obtenido para ese mismo campo durante la anterior extracción. Dicho valor se pasa como segunda posición del array.  La mayoría de calculadores no están diseñados para manipular directamente los campos (a excepción de los que se inicialicen con el parámetro *extracted_data* como ya se ha indicado) sino únicamente para calcular el valor de manera que por configuración se pueda asignar el valor al campo preciso. Esto permite reutilizar los calculadores genéricos en múltiples ocasiones (ver el apartado Configuracion para conocer como configurar este sistema de cálculo). 

## Configuración
La biblioteca *jportada_auto_news_extractor_lib* incluye varios sistemas de configuración que se complementan entre sí. El sistema se inicializa utilizando parámetros pasados ​​a través de la línea de comandos o a través de un archivo de configuración estándar (por ejemplo, `.ini`, `.properties`). Este archivo contiene atributos y sus valores separados por un carácter igual. Además, para los enfoques basados ​​en expresiones regulares, la biblioteca admite un conjunto de archivos de configuración almacenados en directorios, lo que permite la definición de expresiones regulares parciales. Estas pueden combinarse para crear expresiones complejas. A este tipo de configuración la llamaremos _conjunto de expresiones regulares_ o systema _regex_ y generalmente se ubicará en el directorio "regex", aunque existe un atributo de configuración inicial que pude asignar otra ubicación.

Existe todavía un tercer sistema de configuración específico para definir la extracción. Tiene formato JSON y generalmente se encuentra en un archivo llamado _extractor_config.json_, pero de nuevo, desde la configuración inicial, puede especificarse el nombre y ruta donde se ha ubicado. 

Seguidamente, describiremos con más detalles estos 3 sistemas  de configuración.

### Inicialización o configuración inicial

El sistema se puede inicializar mediante argumentos de línea de comandos o un archivo de configuración (`.ini`, `.properties`). Por defecto, la biblioteca busca un fichero llamado _init.properties_ en el directorio de ejecución o en el subdirectorio llamado _config_, pero se le puede pasar otra ubicación usando el argumento -c [RUTA_INIT_PROPERTIES] desde el sistema. Casi todos los atributos permitidos en el fichero se pueden pasar usando el sistema (consola). De esta forma se puede decidir qué argumentos se pasan desde el fichero y qué otros desde el sistema. En caso de que se pasaran argumentos repetidos por fichero y consola, estos últimos tendría siempre prioridad sobre los definidos en el fichero. Desde la consola los atributos a pasar son:

**-h**, **--help** show this help message and exit
 
**-c** *[INIT_CONFIG_FILE]*, **--init_config_file** *[INIT_CONFIG_FILE]*  Camino donde se encuentra el archivo de configuración  (default: config)
 
**-d** *[ORIGIN_DIR]*, **--origin_dir** *[ORIGIN_DIR]*  Directorio de dónde leer los archivos OCR con las  noticias
 
**-o** *[OUTPUT_FILE]*, **--output_file** *[OUTPUT_FILE]*  Camino al archivo de salida. Por ejemplo: -o c:  /directorio/nombre_archivo
 
**-a** *[APPENDOUTPUTFILE]*, **--appendOutputFile** *[APPENDOUTPUTFILE]*  Indica si se desea añadir los barcos extraídos al final del archivo de salida o se crea un nuevo  archivo en cada extracción. Solo acepta los valores  '[s]i', '[y]es', '[c]ert', '[t]rue' como verdaderos. El resto de valores se consideran falsos.
 
**-x** *[FILE_EXTENSION]*, **--file_extension** *[FILE_EXTENSION]*  Indica qué extensión deben tener los archivos en  leer
 
**-r** *[REGEXBASEPATH]*, **--regexBasePath** *[REGEXBASEPATH]*  Directorio donde se encuentran especificadas las  expresiones regulares del análisis 
 
**-f** *[FACT_MODEL]*, **--fact_model** *[FACT_MODEL]* Indica qué tipo de hecho o noticia que se deberá analizar. En el caso del proyecto PorTAda, el tipo de hecho es _boatfacts_.
 
**-n** *[NEWSPAPER]*, **--newspaper** *[NEWSPAPER]* Indica qué nombre del periódico usado para extraer la notícia (db, sm, lp, dm, en, ...).
 
**-oe** *[OCR_ENGINE_MODEL]*, **--ocr_engine_model** *[OCR_ENGINE_MODEL]* Permite indicar qué modelos de expresiones regulares es necesario aplicar, en caso de que el motor OCR se comporte de manera específica.
 
**-p** *[PARSE_MODEL]*, **--parse_model** *[PARSE_MODEL]*  Indica qué modelos de analizador (parser) es necesario usar. Esto es, un nombre identificador del tipo de patrón con el que está escrita la noticia a extraer.
 
**-pcf** *[PARSER_CONFIG_JSON_FILE]*, **--parser_config_json_file** *[PARSER_CONFIG_JSON_FILE]* Indica cuál es el archivo JSON de configuración del exctractor.

**-tfb_pck** *[TARGET_FRAGMENT_BREAKER_PROXY_PACKAGES_TO_SEARCH]*, **--target_fragment_breaker_proxy_packages_to_search** *[TARGET_FRAGMENT_BREAKER_PROXY_PACKAGES_TO_SEARCH]* Indica en qué paquetes el proxy buscará los distintos enfoques de los segregadores de fragmentos-objetivo. 

**-iub_pck** *[INFORMATION_UNIT_BUILDER_PROXY_PACKAGES_TO_SEARCH]*, **--information_unit_builder_proxy_packages_to_search** *[INFORMATION_UNIT_BUILDER_PROXY_PACKAGES_TO_SEARCH]* Indica en qué paquetes el proxy buscará los distintos enfoques de los constructores de unidades de información. 

**-dex_pck** *[DATA_EXTRACT_PROXY_PACKAGES_TO_SEARCH]*, **--data_extract_proxy_packages_to_search** *[DATA_EXTRACT_PROXY_PACKAGES_TO_SEARCH]* Indica en qué paquetes el proxy buscará los distintos enfoques de los extractores de información. 
 
**-decb_pck** *[DATA_EXTRACT_CALCULATOR_BUILDER_PACKAGES_TO_SEARCH]*, **--data_extract_calculator_builder_packages_to_search** *[DATA_EXTRACT_CALCULATOR_BUILDER_PACKAGES_TO_SEARCH]* Indica en qué paquetes el proxy buscará las distintas clases de calculadores de campos. 
 
**-fbapp** *[FRAGMENT_BREAKER_APPROACH]*, **--fragment_breaker_approach** *[FRAGMENT_BREAKER_APPROACH]*  Indica qué enfoque metodológico se usa para separar los fragmentos-objetivo. Actualmente, solo en enfoque "regex" (basado en expresiones regulares) se encuentra implementado.
 
**-exapp** *[EXTRACTOR_APPROACH]*, **--extractor_approach** *[EXTRACTOR_APPROACH]*  Indica qué enfoque metodológico se utiliza para
 hacer la extracción. Actualmente, solo en enfoque "regex" (basado en expresiones regulares) se encuentra implementado.
 
**-rd** *[RUN_FOR_DEBUGGING]*, **--run_for_debugging** *[RUN_FOR_DEBUGGING]* Indica si es necesario ejecutar el proceso en modo  depuración o en modo normal. Los valores: '[s]i', '[y]es', '[c]ert', '[t]rue', '[v]ertader' se toman como valores ciertos, cualquier otro valor se considerará falso.

En el fichero de configuración se admiten todos los argumentos aceptados por consola en su versión larga. Además, dicho fichero acepta otros parámetros relativos al sistema de registro (logs).

### conjunto de expresiones regulares
A fin de poder generar expresiones regulares complejas, la biblioteca _jportada_auto_news_extractor_lib_ permite definir múltiples ficheros con expresiones regulares parciales que pueden ser usadas para componer nuevas expresiones regulares, las cuales podrían ser usadas de nuevo, recursivamente, como componentes de otras expresiones. 

#### Composición de expresiones regulares complejas

Una expresión compuesta podría ser: 
```
^(.*{##embarcaciones##} {##llegadas##} .{2,7} {##puerto##}.{8,25})\s+$
```

Esta expresión buscaría el contenido del fichero _embarcaciones.regex_ y reemplazaría la posición ocupada por `{##embarcacione##}` con el contenido encontrado en el fichero. También buscaría el fichero _llegadas.regex_ y el fichero _puerto.regex_ realizando la misma operación de reemplazo. 

Imaginemos que el fichero _embarcaciones.regex_ contuviera la expresión:
```
[EA]{2,3}barca.{2,4}nes
```

Que el contenido de _llegadas.regex_ fuera:
```
(?:(?:[|i¡l][|i¡l])|(?:[UHN]))[eoa]g[aoeu]d..

```

Y el de _puerto.regex_ fuera:
```
p[uo][eo]rt[oe]
```

La expresión final conseguida con el ejemplo anterior sería:
```
^(.*[EA]{2,3}barca.{2,4}nes (?:(?:[|i¡l][|i¡l])|(?:[UHN]))[eoa]g[aoeu]d.. .{2,7} p[uo][eo]rt[oe].{8,25})\s+$
```

#### Directorios de búsqueda de los archivos de expresiones regulares

Cabe tener en cuenta que la biblioteca _jportada_auto_news_extractor_lib_ dispone de un sistema de búsqueda del los archivos (.regex) con las expresiones a sustituir, bastante flexible. Estos archivos se encuentran ubicados en diversos directorios ramificados a partir de un directorio raíz de manera que forman una estructura jerárquica. 

![Estructura jerárquica de la ubicación de los archivos .regex](media/jerarquiaRegex.png)

La jerarquía de directorios está diseñada en 4 niveles de profundidad:
1. Nivel 0 (raíz): Se ubican archivos con expresiones regulares muy genéricas, las cuales puedan usarse como componentes de otras expresiones aplicables a cualquier tipo de noticias.
2. Nivel 1: Específico para noticias de un tipo determinado. Por ejemplo, noticias sobre hechos de embarcaciones (*boatfacts*), como entradas a puerto, descargas, etc.
3. Nivel 2: Específico para el tratamiento concreto que un determinado periódico hace sobre un tipo de noticia. Por ejemplo, la estructura específica balo la que el Diario de Barcelona agrupa las noticias sobre barcos.
4. Nivel 3: Específico para soportar el modelo extractor. Permite definir, o bien expresiones regulares muy específicas del modelo, o bien las expresiones regulares iniciales a partir de las cuales el sistema compondrá la expresión regular compleja con la que hacer la extracción.

 Las expresiones regulares raíz, también llamadas iniciales o principales, porque son la primera expresión compuesta a partir de la cual, recursivamente, se va a generar la expresión final, necesita un archivo auxiliar con el mismo nombre, pero con extensión "_.options_", para definir las opciones (banderas) del proceso de búsqueda de la expresión siguiendo las notaciones estandarizadas:  g (búsqueda global), m (búsqueda multilínea), i (búsqueda sin distinguir entre mayúsculas o minúsculas - case **i**nsensitive), s (búsqueda de saltos de línea incluidos, se toma toda la cadena como si fura una línea única), U (la búsqueda soporta los caracteres unicode), u (si está marcada la opción 'i', los caracteres unicode especiales se buscan también sin tener en cuanta las mayúsculas o minúsculas).
 
El sistema garantiza que los archivos encuentren dentro de la estructura _regex_, sin especificar la ubicación, conociendo solamente el nombre. La búsqueda se realiza desde el nivel más específico hacia afuera, lo que permite flexibilidad para reemplazar expresiones regulares genéricas por expresiones regulares más específicas.

#### Expresiones regulares alternativas

El contenido de los ficheros .regex debe ser una expresión regular válida con dos excepciones: los componentes de sustitución que siempre tendrán el formato `{##nombre_archivo##}` y los saltos de línea, que al hacer la composición, se tomarán como  expresiones alternativas. Esto es, que un fichero conteniendo:

```
E[mn]b.*[eo][s5]
[EA]{2,3}barca.{2,4}nes
.{1,3}barc.{1,2}c[i¡Il1][oec]n[eosc]
```
Al resolverse se construiría la expresión compleja siguiente:
```
(:?E[mn]b.*[eo][s5])|(:?[EA]{2,3}barca.{2,4}nes)|(:?.{1,3}barc.{1,2}c[i¡Il1][oec]n[eosc])
```
Esta "sintaxis" facilita mucho la creación de expresiones regulares muy complejas usando las propiedades de la sustitución y la búsqueda descritas en loas apartados anteriores, con una mirada más "humana", en el sentido de comprender e interpretar rápidamente las diferentes partes de la expresión compleja.

### Conjunto de Prompts para OpenAI

[==TO DO ...==]

### Configuración de los extractores de contenido

Los extractores o analizadores de contenido orientados a la extracción, se configurarán mediante un fichero JSON, cuya estructura permite gestionar la instanciación y ejecución  de uno a más extractores, ya tengan enfoque "regex" u "openAI". 

A menudo, la información a extraer puede responder a más de un patrón textual dentro de una misma noticia, sección o periódico. Ello nos obliga a trabajar con más de un analizador (uno para cada patrón de texto existente). Por ejemplo, en el Diario de Barcelona, en la misma sección de embarcaciones llegadas conviven dos tipos de patrones textuales, aquellos que detallan las características del viaje, de la embarcación y la carga transportada: "De [PUERTO_DE SALIDA] [, ESCALA[, ... [y ULTIMA_ESCALA]]] en [TIEMPO] [DIAS_HORAS], [TIPO_EMBARCACION] [NOMBRE_EMBARCACION]..." , y los que informa de las embarcaciones de cabotaje, que en lugar de detallar cada embarcación, informan del número de barcos y la carga que llevan entre todos ellos. En este caso, el patrón textual es: "Además, [NUMERO_DE_EMBARCACIONES] buques de la costa de este principado se dirigen a puerto  con [DETALLE_DE_LA_CARGA]".  Al ser patrones tan diferentes, será necesario definirlos por separado.

En el atributo llamado "_parse_model_" del fichero de configuración (*init.properties*) debe detallarse la lista de analizadores para la extracción de los diferentes patrones, indicando los nombres de estos separados por coma. El nombre es solo un identificador y puede tomar cualquier valor. La única restricción es que deben coincidir los nombres definidos en el atributo  "_parse_model_", con las claves indicadas en el fichero de configuración JSON. Imaginemos que el atributo parse_model se encuentra definido como: `parse_model=[boatdata.extractor,boatcosta.extractor]` el fichero de configuración de los analizadores deberá contener estas dos claves y cada una de ellas describirá un objeto JSON con la configuración específica:
```json
{
    "boatdata.extractor": {
		    ...
    },
    "boatcosta.extractor": {
		    ...
    }
}   
```

#### Configuración de un  analizador de tipo *regex*

La configuración de cada analizador tiene formato de objeto JSON con los siguientes campos:
 - **field_version**:  Indica la versión de nombres de campos usada en esta configuración. Por ejemplo: 'boat_fact-00.00.00'".
 - **constants**: Es un objeto JSON con el conjunto de constantes (nombre de la clave y valor) necesarias para configurar este extractor o sus calculadores. Por ejemplo: 
```json
{
	"arrival_port": "Barcelona", 
	"puertos_por_id":{
		"BCN":"Barcelona", 
		"BUE":"Buenos Aires", 
		"HAV":"La Habana",
		"MAR":"Marsella"
	}
}
```
<dl><dd>
Como puede verse en el ejemplo, cada constante contener datos simples o  datos compuestos.
</dd></dl>

 - **config**: Este atributo tiene formato de _array_ y define múltiples niveles de extracción.

Veamos ahora qué significa definir múltiples niveles de extracción y como especificarlos. 

##### Relación jerárquica del contenido

En muchas ocasiones la información escrita mantiene cierta relación jerárquica. Por ejemplo, en la imagen siguiente se puede ver que la información del título hace referencia a todas las entradas de la sección. Así podemos afirmar que todas las entradas de las embarcaciones siguientes se produjeron el día anterior a la fecha de publicación del diario (ayer). Por otro lado, también podemos ver que bajo el subtítulo de mercantes españolas (resaltado en amarillo) se informan de un conjunto de entradas, todas ellas embarcaciones españolas, aunque en el texto no aparezca esa información. De hecho, deducimos que todas las embarcaciones resaltadas en amarillo son españolas, la resaltada en naranja es oldenburguesa y las de color azul inglesas.

![Ejemplo de jerarquía en texto escrito](media/mostraJerarquiaText.png)

Esta deducción responde a la estructura implícita en la distribución textual. Así podemos concluir que desde el primer subtítulo ("mercantes españolas" en el ejemplo) hasta el siguiente ("id. oldenburguesa") las embarcaciones comparten la bandera que se extraiga del subtítulo. Las que se encuentran  entre el segundo y tercer subtitulo, en cambio, comparten la bandera extraída del subtítulo ("oldenburguesas") y las que se encuentran debajo del tercer subtítulo hasta el final deberán ser "inglesas".

En este caso, se necesitará más de una expresión regular para analizar y extraer toda la información contenida en la sección. Por un lado, necesitaremos, al menos,  una expresión regular que identifique los subtítulos y extraiga la bandera y por otro, una expresión regular que identifique y extraiga el resto de información para el texto que quede entre subtítulo y subtítulo.  Por tanto,  el atributo *config* de fichero JSON podrá tener varias especificaciones dependiendo de cuantos niveles de jerárquicos tenga nuestro texto. 

##### Funcionamiento del extractor basado en expresiones regulares

Debemos entender el proceso de análisis basado en expresiones regulares como un proceso cíclico de búsqueda parcial del patrón textual  identificado por la expresión regular. Cada vez que se encuentra el patrón dentro del texto, se extrae la información  y acto seguido se sigue la búsqueda en el texto que queda por analizar hasta llegar al final. El extractor de la biblioteca _jportada_auto_news_extractor_lib_ lo que hace, es aprovechar este proceso para que, después de cada búsqueda, se almacene el texto analizado en el que no se ha encontrado el patrón buscado, par aplicar en él, una nueva búsqueda del extractor de siguiente nivel. 

Veamos un ejemplo gráfico para ilustrarlo. Imaginemos que nuestro texto fuera como el gráfico de colores de la imagen y que la jerarquía, en lugar de ir de arriba a abajo, fuera de izquierda a derecha. Por tanto, la información de recuadro azul pertenecería a todo el texto (jerarquía más alta). Los recuadros morados representarían el segundo nivel de la jerarquía y los naranjas el tercero. Así, cada recuadro naranja, además de su información, debería tener también la que le corresponda de morado y la situada en el color azul.

![Ejemplo de jerarquía con colores](media/jerarquiaColores.png) 

Cuando el proceso de extracción de la aplicación comienza a procesar, se escoge el primer extractor de la jerarquía, el cual buscará todos los patrones azules existentes en el texto. Al encontrar el primero al inicio del texto, extrae la información y continua su búsqueda con el texto restante.  

![Ejemplo de jerarquía con colores](media/jerarquiaColores2.png) 

Al no haber más texto con el patrón azul, se reserva la información extraída y se cambia al extractor de segundo nivel, el cual detectará patrones morados. Encontrará el primero al inicio del texto analizado, extraerá la información y continuará buscando.

![Ejemplo de jerarquía con colores](media/jerarquiaColores3.png) 

Se encuentra el siguiente patrón morado, pero como no se encuentra al inicio del texto, se extrae su información (asociándola a la extraída del nivel anterior) y se reserva el texto donde no se ha encontrado nada, para realizar un análisis de tercer nivel cuando se acabe con el del segundo. Se sigue buscando.

![Ejemplo de jerarquía con colores](media/jerarquiaColores4.png) 

Se repite la operación con el siguiente patrón morado.

![Ejemplo de jerarquía con colores](media/jerarquiaColores5.png) 

 Al no quedar más patrones morados se reserva el texto para el siguiente nivel.

![Ejemplo de jerarquía con colores](media/jerarquiaColores6.png) 

Al activar el analizador del tercer nivel (para buscar patrones naranjas), encuentra el primer texto al inicio, lo reserva y asocia a la información encontrada en niveles anteriores. La búsqueda sigue.

![Ejemplo de jerarquía con colores](media/jerarquiaColores7.png) 

Se repite la operación con el último texto reservado en el primer bloque de morados. La búsqueda continua con el segundo bloque de morados.

![Ejemplo de jerarquía con colores](media/jerarquiaColores8.png) 

El proceso se repite para cada bloque hasta conseguir la información completa de todos ellos.

![Ejemplo de jerarquía con colores](media/jerarquiaColores9.10.png) 

##### Copia de datos en el mismo nivel

Una vez visto con detalle el proceso de extracción en textos jerárquicos, vamos a plantear otra posible solución para las jerarquías que no se repiten. La biblioteca _jportada_auto_news_extractor_lib_ permite forzar la copia de los campos que se indique, entre búsquedas de un mismo nivel jerárquico. En este tipo de noticias, los mensajes pueden ser bastante crípticos, debido a la necesidad de reducir el texto tanto como sea posible. Esto hace que, a veces, alguna información aparecida en anteriormente, se suponga implícita y no aparezca en la nueva entrada. No pasa siempre, pero puede darse el caso. Si ocurre deberemos forzar la copia. Podemos aprovechar, también,  esta característica, para ahorrarnos la creación de un nivel de extracción cuando la información de un nivel superior no se repita nunca (aparezca solamente una vez). Siguiendo con el ejemplo de colores, si al patrón de búsqueda de morados le añadimos una alternativa consistente en buscar azules y morados. Es decir,  
```
{##azules##}\n{##morados##}
{##morados##}
```
Podemos conseguir la información de los azules desde el patrón morado, evitando así la creación del extractor específico de los azules. Entonces, para que dicha información se extienda a todas las demás entradas moradas, deberemos forzar una copia de los campos propiamente azules. 

Por tanto, tenemos dos maneras válidas de tratar la información jerárquica que solo se aparece una vez, o bien creamos un extractor específico que obtenga su información, o bien la extraemos desde el extractor del nivel siguiente y forzamos su copia.

##### Configuración de cada nivel de extracción

Para cada uno de los extractores se deberá definir en un formato de objeto JSON las siguientes características:

 - **approach_type**: Permite indicar el enfoque del extractor. Admite 'regex' o 'openai'. Es necesario clarificar que la siguiente configuración es específica para 'regex' pues la correspondiente a 'openai' se muestra en el apartado relativo a la configuración de los extractores openai.
 - **configuration**: es un objeto que contendrá la especificación siguiente: 
	 - **main_regex**: Nombre del archivo '.regex' inicial que originará toda la expresión de extracción final.
	 - **max_groups**: Este es un dato numérico e indica el número máximo de grupos que la expresión manejara. Como mínimo habría que indicar el número de campos que esta expresión obtiene, aunque, si la expresión principal necesita varias alternativas, el valor será un múltiplo del número de campos a extraer (número de campos * número de alternativas).
	 - **fields_to_extract**:  _Array_ con la especificación de la extracción de cada campo en el mismo orden que aparezcan en el texto
	 - **fields_to_calculate**: _Array_ con la especificación del cálculo a realizar de aquellos campos en que sea necesario.

Para cada campo a extraer (ítem de fields_to_extract), deberá indicarse:
 - **key**: Nombre de la categoría o campo que se dará al valor extraído en el grupo de la exterior regular correspondiente a la misma posición que esta definición tenga en el _array_ 'fields_to_extract'.
 - **temporary_field**: Indica si el nombre definido en 'key' será temporal o se corresponderá con alguno definidor en la versión del modelo de extracción identificado por 'field_version'.
 - **default_value**: Valor que queremos darle al campo en caso de que la expresión regular no sea capaz de identificar su valor. Este es importante para dar un valor específico en aquellos campos que se utilicen para calcular otros, a fin de evitar problemas en el procesamiento del cálculo, pero también es importante para asignar un valor que permita distinguir los campos no encontrados de los encontrados. Por ejemplo, "???" permitiría distinguir de un solo vistazo los campos encontrados de los no encontrados.
 - **copy_last_value**: Este atributo necesita un valor booleano (true/false) y permite reducir el número de extractores a añadir en 'config'. Un valor de true, indica que su valor se copiará a la siguiente extracción encontrada por la  expresión regular. Así, la información perteneciente al título principal, puede irse copiando al resto de su misma categoría sin necesidad de establecer  un extractor para la categoría superior.

Para cada campo a calcular (ítem de fields_to_calculate), deberá indicarse:
 - **calculator**: nombre que identifica el calculador para que el proxy pueda encontrarlo.
 - **key**:  nombre del campo donde volcará el valor calculado por este calculador. 
 - **temporary_field**: Indica lo mismo que su homónimo de "_ fields_to_extract_". En caso de que ya se haya definido anteriormente, no será necesario repetir aquí la información.
 - **init_data**: Este es un dato opcional. Si aparece debe tenar formato _array_. Indicará las múltiples inicializaciones que este calculador necesita. Serán valores válidos: "configuration", "parser_id", "constants" o "extracted_data" definidos en el apartado [Sistema del proxy para las utilidades FieldCalculator](https://github.com/portada-git/developers_portada_project_documentation/blob/main/ManualDesarrolladores.md#sistema-del-proxy-para-las-utilidades-fieldcalculator).
 - **params**: Este dato es opcional en función de si el calculador necesita que se le pasen parámetros o no. Si aparece, debe contener la especificación de cada parámetro en formato de objeto JSON separados por comas. La especificación de cada parámetro contiene la indicación del tipo de parámetro y el valor del mismo. Los tipos permitidos actualmente son: literal, fieldValue i fieldName. El tipo literal indica que el valor del mismo puede ser cualquiera y no está sujeto a comprobación de las actualizaciones de la versión. El tipo fieldValue indica que el valor contendrá el nombre del campo del cual se quiere extraer el valor antes de ejecutar el calculador. Admite los prefijos extracted_data o last_extracted_dat según se desee el valor recién extraído o el valor obtenido de la última extracción completa. Por ejemplo si se especifica `["extracted_data.master_role", "last_extracted_data.master_role"]`se pasará al calculador especificado, el rol del responsable obtenido en el proceso de extracción (supongamos 'id.') y la misma categoría, pero cuyo valor fue obtenido en la extracción de la embarcación leída justo antes de la actual (supongamos 'cap.'). El tipo fieldName indica que el valor del parámetro será el nombre de un campo existente durante la extracción. Es importante usar este tipo para facilitar la verificación y actualización de los campos de fichero de configuración de forma automática.
 - **fieldParams**: Este dato es opcional. Si aparece, debe pasarse los nombres de los campos de los que se quiera obtener su valor, precedidos de _extracted_data._ o _last_extracted_data._,  según se desee el valor recién extraído o el valor obtenido de la última extracción completa. Por ejemplo si se especifica `["extracted_data.master_role", "last_extracted_data.master_role"]`se pasará al calculador especificado, el rol del responsable obtenido en el proceso de extracción (supongamos 'id.') y la misma categoría, pero cuyo valor fue obtenido en la extracción de la embarcación leída justo antes de la actual (supongamos 'cap.'). Aunque se mantiene este formato, se aconseja usar la versión de *params* en su lugar.
 - **literalParams**: Este dato es opcional y corresponderá a la lista de valores literales que se desee pasar como parámetros al calculador. Se acepta cualquier valor literal i se define en formato _array_. Por ejemplo: `["La Habana"]. Aunque se mantiene este formato, se aconseja usar la versión de *params* en su lugar.

##### Ejemplo de configuración completo
 
 Sirva de ilustración de lo descrito, el siguiente ejemplo de una configuración completa:
 
```json
 {
    "boatdata.extractor": {
        "field_version": "boat_fact-00.00.00",
        "constants": {"arrival_port": "Barcelona"},
        "config": [
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 15,
                    "fields_to_extract": [
                        {
                            "temporary_field": true,
                            "default_value": "y",
                            "copy_last_value": true,
                            "key": "time_of_arrival"
                        },
                        {
                            "temporary_field": true,
                            "default_value": "mercante",
                            "copy_last_value": true,
                            "key": "purposeType"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_flag"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "TimeOfArrivalRelativeToPublicationCalculator",
                            "temporary_field": true,
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "time_of_arrival"
                        },
                        {
                            "calculator": "ElapsedTimeFromArrivalToPublicationCalculator",
                            "temporary_field": true,
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "elapsed_days_from_arrival"
                        }
                    ],
                    "main_regex": "flag"
                }
            },
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 10,
                    "fields_to_extract": [
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_departure_port"
                        },
                        {
                            "default_value": "??",
                            "copy_last_value": false,
                            "key": "ship_travel_time"
                        },
                        {
                            "default_value": "?",
                            "copy_last_value": true,
                            "key": "ship_travel_time_unit"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_type"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_name"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_tons"
                        },
                        {
                            "temporary_field": true,
                            "default_value": "t.",
                            "copy_last_value": false,
                            "key": "ship_tons_unit"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_master_role"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_master_name"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_cargo_list"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "DataFromConstantCalculator",
                            "init_data": ["constants"],
                            "key": "ship_arrival_port",
                            "literalParams": ["arrival_port"]
                        },
                        {
                            "calculator": "PortOfCallsFromOriginPortCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id",
                                "extracted_data"
                            ],
                            "key": "ship_port_of_call_list",
                            "literalParams": ["ship_departure_port"]
                        },
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.ship_travel_time",
                                "last_extracted_data.ship_travel_time"
                            ],
                            "key": "ship_travel_time"
                        },
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.ship_travel_time_unit",
                                "last_extracted_data.ship_travel_time_unit"
                            ],
                            "key": "ship_travel_time_unit"
                        },
                        {
                            "calculator": "ShipArrivalDateCalculator",
                            "fieldParams": [
                                "extracted_data.elapsed_days_from_arrival",
                                "extracted_data.publication_date"
                            ],
                            "key": "ship_arrival_date"
                        },
                        {
                            "calculator": "ShipDepartureDateCalculator",
                            "fieldParams": [
                                "extracted_data.ship_arrival_date",
                                "extracted_data.ship_travel_time",
                                "extracted_data.ship_travel_time_unit"
                            ],
                            "key": "ship_departure_date"
                        }
                    ],
                    "main_regex": "boat_fact"
                }
            }
        ]
    },
    "boatcosta.extractor": {
        "field_version": "boat_fact-00.00.00",
        "constants": {"arrival_port": "Barcelona"},
        "config": [
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 15,
                    "fields_to_extract": [
                        {
                            "temporary_field": true,
                            "default_value": "y",
                            "copy_last_value": true,
                            "key": "time_of_arrival"
                        },
                        {
                            "temporary_field": true,
                            "default_value": "mercante",
                            "copy_last_value": true,
                            "key": "purposeType"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_flag"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "TimeOfArrivalRelativeToPublicationCalculator",
                            "temporary_field": true,
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "time_of_arrival"
                        },
                        {
                            "calculator": "ElapsedTimeFromArrivalToPublicationCalculator",
                            "temporary_field": true,
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "elapsed_days_from_arrival"
                        }
                    ],
                    "main_regex": "flag"
                }
            },
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 9,
                    "fields_to_extract": [
                        {
                            "default_value": "??",
                            "copy_last_value": false,
                            "key": "ship_amount"
                        },
                        {
                            "default_value": "??",
                            "copy_last_value": false,
                            "key": "ship_origin_area"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": true,
                            "key": "ship_cargo_list"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "DataFromConstantCalculator",
                            "init_data": ["constants"],
                            "key": "ship_arrival_port",
                            "literalParams": ["arrival_port"]
                        },
                        {
                            "calculator": "ShipArrivalDateCalculator",
                            "fieldParams": [
                                "extracted_data.elapsed_days_from_arrival",
                                "extracted_data.publication_date"
                            ],
                            "key": "ship_arrival_date"
                        }
                    ],
                    "main_regex": "unknown_boat_fact"
                }
            }
        ]
    }
}
```

#### Configuración de un  analizador de tipo *openai*		

El analizador openai implementado en el proyecto portADa permite ser usado en cualquier nivel correspondiente a la jerarquía del texto a analizar, con independencia del tipo usado en los otros niveles. Esto significa que podrá configurarse un conjunto de analizadores mixtos (expresiones regulares / openAI).

La configuración relativa a los analizadores "openai" siguen la misma estandarización que el resto de analizadores. Esto es, un objeto JSON con dos atributos principales (_aproach_type_, que deberá tener asignado el valor "openai" y el campo _configuration_, el cual contendrá propiamente la configuración específica para que openAI pueda realizar la extracción de la información  correspondiente al nivel para el cual esté configurado.

El campo configuración es un objeto JSON con los atributos siguientes:
  - __parse_by_paragraphs__: Es de tipo booleano y permite indicar que el análisis se realizará párrafo  a párrafo o bien usando todo el texto disponible. Si su valor es _true_ el texto del nivel a analizar se romperá en párrafos y se pasará a openAI cada uno de los párrafos de forma independiente. Por contra, si su valor fuera _false_, el texto entero del nivel, se pasaría íntegro a openAI.
  - __save_parsed_data__: Es otro atributo booleano para indicar si se requerirá guardar en el JSON de salida el texto del nivel analizado bajo el atributo  "parsed_text".
  - __model__: Indica el nombre del modelo de openAI que deseamos usar para realizar la extracción, por ejemplo "gpt-4o-mini".
  - __model_config__: indica la configuración para el modelo escogido de "openai". Tiene formato JSON y se compone de los siguientes atributos: *temperature*, *max_tokens*, *top_p*,  *frequency_penalty* y *presence_penalty*
  - __ai_instructions__: Corresponde a las instrucciones específicas usadas para indicar a openai como debe realizar la extracción. Se trata de un campo compuesto conteniendo:
    - __messages_config__: Es una plantilla del mensaje a enviar en el prompt de openai con el contenido que sigue:
      ```json
      "messages_config": {
         "system": {
             "role": "system",
                 "content": "Eres un asistente experto en extraer información estructurada de notas sobre entradas de barcos a puerto. Debes responder EXCLUSIVAMENTE con un objeto JSON válido que contenga los campos solicitados. Si no encuentras información para algún campo, debes responder con el valor null en ese campo."
         },
         "template": {
             "role": "user",
             "content": "Extrae la siguiente información del evento de entrada de barco descrita en la nota, utilizando el formato JSON exacto: {json_template}. Aquí está la definición de cada clave: {field_definitions}. Ejemplos: {input_example}. Texto de donde extraer la información: {input_text}"
         }
      }
      ```
    - __json_template__: una plantilla básica del objeto json esperado para la extracción.
    - __json_schema__: un schema de datos en formato JSON representado el esquema que se espera que sea devuelto por openai como resultado de la extracción.
    - __examples__: contiene un conjunto de ejemplos de la extracción, para mejorar la eficacia de openai.
    - __field_definitions__: contiene la definición de los campos que openai debe encontrar y extraer en el texto que lse le pasa para la extracción.
  - __fields_to_assign__: indica las instrucciones para assignar los campos extraidos por openai a la estructura de datos que se va a devolver. Esto permite asignar campos con nombres distintos a los que openai ha usado i también prepararlos para aplicar calculadores a los campos asignados. Este campo és un array cuyos ítems son objetos con 2 atributos: source para indicar el nombre del campo que openai ha utilizado para la extracción y target para indicar el nombre del campo al que se asignará el valor extraido.
  - __fields_to_calculate__: permite definir los calculos a realizar en los campos asignados. Tiene la misma estructura que la usada en los extractores de tipo "regex". Es decir:
     - **calculator**: nombre que identifica el calculador para que el proxy pueda encontrarlo.
     - **key**:  nombre del campo donde volcará el valor calculado por este calculador. 
     - **temporary_field**: Indica lo mismo que su homónimo de "_ fields_to_extract_". En caso de que ya se haya definido anteriormente, no será necesario repetir aquí la información.
     - **init_data**: Este es un dato opcional. Si aparece debe tenar formato _array_. Indicará las múltiples inicializaciones que este calculador necesita. Serán valores válidos: "configuration", "parser_id", "constants" o "extracted_data" definidos en el apartado [Sistema del proxy para las utilidades FieldCalculator](https://github.com/portada-git/developers_portada_project_documentation/blob/main/ManualDesarrolladores.md#sistema-del-proxy-para-las-utilidades-fieldcalculator).
     - **params**: Este dato es opcional en función de si el calculador necesita que se le pasen parámetros o no. Si aparece, debe contener la especificación de cada parámetro en formato de objeto JSON separados por comas. La especificación de cada parámetro contiene la indicación del tipo de parámetro y el valor del mismo. Los tipos permitidos actualmente son: literal, fieldValue i fieldName. El tipo literal indica que el valor del mismo puede ser cualquiera y no está sujeto a comprobación de las actualizaciones de la versión. El tipo fieldValue indica que el valor contendrá el nombre del campo del cual se quiere extraer el valor antes de ejecutar el calculador. Admite los prefijos extracted_data o last_extracted_dat según se desee el valor recién extraído o el valor obtenido de la última extracción completa. Por ejemplo si se especifica `["extracted_data.master_role", "last_extracted_data.master_role"]`se pasará al calculador especificado, el rol del responsable obtenido en el proceso de extracción (supongamos 'id.') y la misma categoría, pero cuyo valor fue obtenido en la extracción de la embarcación leída justo antes de la actual (supongamos 'cap.'). El tipo fieldName indica que el valor del parámetro será el nombre de un campo existente durante la extracción. Es importante usar este tipo para facilitar la verificación y actualización de los campos de fichero de configuración de forma automática.
     - **fieldParams**: Este dato es opcional. Si aparece, debe pasarse los nombres de los campos de los que se quiera obtener su valor, precedidos de _extracted_data._ o _last_extracted_data._,  según se desee el valor recién extraído o el valor obtenido de la última extracción completa. Por ejemplo si se especifica `["extracted_data.master_role", "last_extracted_data.master_role"]`se pasará al calculador especificado, el rol del responsable obtenido en el proceso de extracción (supongamos 'id.') y la misma categoría, pero cuyo valor fue obtenido en la extracción de la embarcación leída justo antes de la actual (supongamos 'cap.'). Aunque se mantiene este formato, se aconseja usar la versión de *params* en su lugar.
     - **literalParams**: Este dato es opcional y corresponderá a la lista de valores literales que se desee pasar como parámetros al calculador. Se acepta cualquier valor literal i se define en formato _array_. Por ejemplo: `["La Habana"]. Aunque se mantiene este formato, se aconseja usar la versión de *params* en su lugar.

Ejemplo completo usando solamente aopenai:
```json
{
    "ai_extractor":{
        "field_version": "boat_fact-00.00.01",
        "constants": {"arrival_port":"Buenos Aires"},
        "config":[
            {
                "approach_type": "openai",
                "configuration": {
                    "parse_by_paragraphs":true,
                    "save_parsed_data":true,
                    "microservice_initializer_file":"/etc/.portada_microservices/ms_init.properties",
                    "model": "gpt-4o-mini",
                    "model_config": {
                        "temperature": 0,
                        "max_tokens": 9000,
                        "top_p": 0,
                        "frequency_penalty": 0,
                        "presence_penalty": 0
                    },
                    "ai_instructions": {
                        "messages_config": {
                            "system": {
                                "role": "system",
                                "content": "Eres un asistente experto en extraer información estructurada de notas sobre entradas de barcos a puerto. Debes responder EXCLUSIVAMENTE con un objeto JSON válido que contenga los campos solicitados. Si no encuentras información para algún campo, debes responder con el valor null en ese campo."
                            },
                            "template": {
                                "role": "user",
                                "content": "Extrae la siguiente información del evento de entrada de barco descrita en la nota, utilizando el formato JSON exacto: {json_template}. Aquí está la definición de cada clave: {field_definitions}. Ejemplos: {input_example}. Texto de donde extraer la información: {input_text}"
                            }
                        },
                        "json_template": {
                            "travel_departure_date": null,
                            "travel_arrival_date": null,
                            "travel_departure_port": null,
                            "travel_port_of_call_list": [],
                            "ship_type": null,
                            "ship_name": null,
                            "ship_tons_capacity": null,
                            "ship_tons_units": null,
                            "ship_flag": null,
                            "master_role": null,
                            "master_name": null,
                            "broker_name": null,
                            "cargo_list": [],
                            "quarantine": null,
                            "forced_arrival": null,
                            "obs": null
                        },
                        "json_schema":{
                          "type": "json_schema",
                          "json_schema": {
                            "name": "ship_entry",
                            "strict": true,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "travel_departure_date": {
                                      "type": "string",
                                      "description": "Fecha de salida del puerto en formato YYYY-MM-DD.",
                                      "nullable": true
                                    },
                                    "travel_arrival_date": {
                                      "type": "string",
                                      "description": "Fecha de llegada al puerto en formato YYYY-MM-DD.",
                                      "nullable": true
                                    },
                                    "travel_departure_port": {
                                      "type": "string",
                                      "description": "Puerto desde el cual salió el barco.",
                                      "nullable": true
                                    },
                                    "travel_port_of_call_list": {
                                        "type": "array",
                                        "description": "Lista de puertos donde el barco hizo escala.",
                                        "nullable": true,
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "port_of_call_place": {
                                                    "type": "string",
                                                    "description": "Puerto donde hizo la escala.",
                                                    "nullable": true
                                                },
                                                "port_of_call_arrival_date": {
                                                    "type": "string",
                                                    "description": "Fecha de llegada al puerto de escala.",
                                                    "nullable": true
                                                }
                                            },
                                            "required": ["port_of_call_place", "port_of_call_arrival_date"],
                                            "additionalProperties": false
                                        }
                                    },
                                    "ship_type": {
                                      "type": "string",
                                      "description": "Tipo de embarcación.",
                                      "nullable": true
                                    },
                                    "ship_name": {
                                      "type": "string",
                                      "description": "Nombre del barco.",
                                      "nullable": true
                                    },
                                    "ship_tons_capacity": {
                                      "type": "string",
                                      "description": "Capacidad de carga del buque en toneladas. Debido a los posibles errores de transcripción del OCR, este dato se expresará como una cadena de caracteres. Si en la transcrición indicara, por ejemplo que el barco tiene una capacidad de 'B7 t.', en este campo deberá trasladarse el valor B7. Si se omitiera este valor dejaras este valor a null",
                                      "nullable": true
                                    },
                                    "ship_tons_units": {
                                      "type": "string",
                                      "description": "Especifica las unidades en las que está expresado las dimensiones del buque. Normalmente toneladas, simbolizadas por la abreviación 't.'",
                                      "nullable": true
                                    },
                                    "ship_flag": {
                                      "type": "string",
                                      "description": "País o nacionalidad bajo cuya bandera navega el barco. Ejemplos: 'español', 'americano', 'oriental'",
                                      "nullable": true
                                    },
                                    "master_role": {
                                      "type": "string",
                                      "description": "Cargo del responsable a bordo. Puede ser 'capitan' abreviado con c. o cap., 'piloto'abreviado con pil. o 'patrón' abreviado con p. o pat.",
                                      "nullable": true
                                    },
                                    "master_name": {
                                      "type": "string",
                                      "description": "Nombre del responsable a bordo.",
                                      "nullable": true
                                    },
                                    "broker_name": {
                                      "type": "string",
                                      "description": "Nombre del agente marítimo.",
                                      "nullable": true
                                    },                                        
                                    "cargo_list": {
                                      "type": "array",
                                      "description": "Lista de mercancías transportadas y sus propietarios.",
                                      "nullable": false,
                                      "items": {
                                        "type": "object",
                                        "properties": {
                                            "cargo_merchant_name": {
                                              "type": "string",
                                              "description": "Es el propietario de la carga o aquella persona a quien dicha carga va destinada.",
                                              "nullable": true
                                            },
                                            "cargo": {
                                                "type": "array",
                                                "description": "Lista de mercancías transportadas.",
                                                "nullable": false,
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "cargo_quantity": {
                                                            "type": "string",
                                                            "description": "Representa la cantidad total de la carga en forma numérica. Se expresa como cadena de caracteres para evitar errores en el JSON si en la cantidad figuran letras en lugar de números debido a errores tipográficos o de transcripció del OCR. Si en la transcrición indicara, por ejemplo '2I pipas aceite', en este campo deberá trasladarse el valor 2I. Si el número no está presente, debe asignarse el valor null.",
                                                            "nullable": true
                                                        },
                                                        "cargo_unit": {
                                                            "type": "string",
                                                            "description": "Expresa las unidades de medida en las que la carga aparece. Ejemplo: 'cargo_unit': 'cj', 'cargo_unit':'barriles', 'cargo_unit': 'id'",
                                                            "nullable": true
                                                        },
                                                        "cargo_commodity": {
                                                            "type": "string",
                                                            "description": "Expresa los distintos productos o tipos de mercancías que transporta el buque. Ejemplo: 'cargo_commodity': 'cristales', 'cargo_commodity': 'id', 'cargo_commodity': 'vino'",
                                                            "nullable": true
                                                        }
                                                    },
                                                    "required": ["cargo_quantity", "cargo_unit", "cargo_commodity"],
                                                    "additionalProperties": false
                                                }
                                            }
                                        },
                                        "required": ["cargo_merchant_name", "cargo"],
                                        "additionalProperties": false
                                    }
                                  },
                                  "quarantine": {
                                    "type": "boolean",
                                    "description": "Información relativa a la existencia de condiciones especiales de la llegada motivadas por circunstancias sanitarias que imponen la cuarentena.",
                                    "nullable": true
                                  },
                                  "forced_arrival": {
                                    "type": "boolean",
                                    "description": "Información sobre la llegada al puerto debido a causas imprevistas, como un arribo forzoso por temporal, avería u otras emergencias.",
                                    "nullable": true
                                  },
                                  "obs": {
                                    "type": "string",
                                    "description": "Notas o comentarios adicionales que aborden aspectos no contemplados en las variables registradas, proporcionando información contextual o relevante sobre el evento.",
                                    "nullable": true
                                  }
                                },
                                "required": [
                                    "travel_departure_date", 
                                    "travel_arrival_date",
                                    "travel_departure_port", 
                                    "travel_port_of_call_list", 
                                    "ship_type", 
                                    "ship_name", 
                                    "ship_tons_capacity", 
                                    "ship_tons_units",
                                    "ship_flag",
                                    "master_role", 
                                    "master_name", 
                                    "broker_name",      
                                    "cargo_list",
                                    "quarantine",
                                    "forced_arrival",
                                    "obs"
                                ],
                                "additionalProperties": false
                            }
                          }
                        },
                        "examples": {
                            "EJEMPLO 1": {
                                "input" : "Fecha de arribo: 4 de enero de 1880; puerto de salida: Pernambuco el 23 de Dbre berg gta portugues Gomez de Castro 147 tons cap Goncalvez à J Cibils con: 40 pip caña, 50 bcas azúcar moscavada 975 bcas 75 1[4 azúcar blanca; á G Schiano 1 baul, 1 balija alhajas.",
                                "output": "{ 'travel_departure_date': '1879-12-23', 'travel_arrival_date': '1880-01-04', 'travel_departure_port': 'Pernambuco', 'travel_port_of_call_list': [], 'ship_type': 'berg gta', 'ship_name': 'Gomez de Castro', 'ship_tons_capacity':  '147', 'ship_tons_units': ' tons', 'ship_flag': 'portugues', 'master_role': 'cap', 'master_name': 'Goncalvez', 'broker_name': 'J Cibils', 'cargo_list': [ { 'cargo_merchant_name': 'J Cibils', 'cargo': [ { 'cargo_quantity': '40', 'cargo_unit': 'pip', 'cargo_commodity': 'caña' }, { 'cargo_quantity': '50', 'cargo_unit': 'bcas', 'cargo_commodity': 'azúcar moscavada' }, { 'cargo_quantity': '975', 'cargo_unit': 'bcas', 'cargo_commodity': 'azúcar blanca' } ] }, { 'cargo_merchant_name': 'G Schiano', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'baul', 'cargo_commodity': null }, { 'cargo_quantity': '1', 'cargo_unit': 'balija', 'cargo_commodity': 'alhajas' } ] } ], 'quarantine': false, 'forced_arrival': false, 'obs': '75 1[4' }"
                            },
                            "EJEMPLO 2": {
                                "input":"Fecha de arribo: 5 de enero de 1880; puerto de salida: Londres Amberes Rio Janeiro y Montevido vapor inglés Horrox 1101 tons cap Eddes á E, Norton con: á Bemberg C. 5 fds bsas 1 bto mtras; J Fulton 15 cj 5 casc provisiones; Parry 115 cj merc. J. Etchegaray 10 fds medias; Tramway Ciudad de Buenos Aires 25 casc herraduras; H. Peltzer 10 cj drogas; Puerto Ensenada 24 btos acero; Ferro C, del Sud 6 cj cristaleria; Moore C.12 cj perfumeria, Hape hnos 6 fds bolsas; Orden 230 cj hojalata 331 bto merc 51 cj id 9 id papel.",
                                "output":"{ 'travel_departure_date': null, 'travel_arrival_date': '1880-01-05', 'travel_departure_port': 'Londres', 'travel_port_of_call_list': [ { 'port_of_call_place': 'Amberes', 'port_of_call_arrival_date': null}, { 'port_of_call_place': ' Rio Janeiro', 'port_of_call_arrival_date': null}, { 'port_of_call_place': ' Montevideo', 'port_of_call_arrival_date': null} ], 'ship_type': 'vapor', 'ship_name': 'Horrox', 'ship_tons_capacity': 1101, 'ship_tons_units': 'tons', 'ship_flag': 'inglés', 'master_role': 'cap', 'master_name': 'Eddes', 'broker_name': 'E. Norton', 'cargo_list': [ { 'cargo_merchant_name': 'Bemberg C.', 'cargo': [ { 'cargo_quantity': '5', 'cargo_unit': 'fds', 'cargo_commodity': 'bsas' }, { 'cargo_quantity': '1', 'cargo_unit': 'bto', 'cargo_commodity': 'mtras' } ] }, { 'cargo_merchant_name': 'J Fulton', 'cargo': [ { 'cargo_quantity': '15, 5', 'cargo_unit': 'cj, casc', 'cargo_commodity': 'provisiones' } ] }, { 'cargo_merchant_name': 'Parry', 'cargo': [ { 'cargo_quantity': '115', 'cargo_unit': 'cj', 'cargo_commodity': 'merc.' } ] }, { 'cargo_merchant_name': 'J. Etchegaray', 'cargo': [ { 'cargo_quantity': '10', 'cargo_unit': 'fds', 'cargo_commodity': 'medias' } ] }, { 'cargo_merchant_name': 'Tramway Ciudad de Buenos Aires', 'cargo': [ { 'cargo_quantity': '25', 'cargo_unit': 'casc', 'cargo_commodity': 'herraduras' } ] }, { 'cargo_merchant_name': 'H. Peltzer', 'cargo': [ { 'cargo_quantity': '10', 'cargo_unit': 'cj', 'cargo_commodity': 'drogas' } ] }, { 'cargo_merchant_name': 'Puerto Ensenada', 'cargo': [ { 'cargo_quantity': '24', 'cargo_unit': 'btos', 'cargo_commodity': 'acero' } ] }, { 'cargo_merchant_name': 'Ferro C. del Sud', 'cargo': [ { 'cargo_quantity': '6', 'cargo_unit': 'cj', 'cargo_commodity': 'cristaleria' } ] }, { 'cargo_merchant_name': 'Moore C.', 'cargo': [ { 'cargo_quantity': '12', 'cargo_unit': 'cj', 'cargo_commodity': 'perfumeria' } ] }, { 'cargo_merchant_name': 'Hape hnos', 'cargo': [ { 'cargo_quantity': '6', 'cargo_unit': 'fds', 'cargo_commodity': 'bolsas' } ] }, { 'cargo_merchant_name': 'Orden', 'cargo': [ { 'cargo_quantity': '230', 'cargo_unit': 'cj', 'cargo_commodity': 'hojalata' }, { 'cargo_quantity': '331', 'cargo_unit': 'bto', 'cargo_commodity': 'merc' }, { 'cargo_quantity': '51', 'cargo_unit': 'cj', 'cargo_commodity': 'id' }, { 'cargo_quantity': '9', 'cargo_unit': 'id', 'cargo_commodity': 'papel' } ] }], 'quarantine': false, 'forced_arrival': false, 'obs': null }"
                            },
                            "EJEMPLO 3": {
                                "input":"Fecha de arribo: 11 de enero de 1880; puerto de salida: Amberes à M. del Pont 51 cj velas; W. Paats 200 cj quesos; F F. 200 cj ginebra; F. Meyer 2 casc vino; H. Koch 58 cj manufacturas; Bemberg C. 36 fds papel; C. Riva 20 btos quesos; J, Lopez 1 cj armas; Verney C, 23 id id, A, Bunge 1 id vino; L, Logegaray 26 id 6 barriles ferreteria; Mallman C. 8 fds lana 1 bto mtras: F. Chás é hijos 61 id cristaleria C. F. Bally 30 id calzado; J. Cadmus 2 cj con: 100,000 francos 15 btos papel 917 rieles 679 btos fierro.",
                                "output":"{ 'travel_departure_date': null, 'travel_arrival_date': '1880-01-11', 'travel_departure_port': 'Amberes', 'travel_port_of_call_list': [], 'ship_type': null, 'ship_name': null, 'ship_tons_capacity': null, 'ship_tons_units': null, 'ship_flag': null, 'master_role': null, 'master_name': null, 'broker_name': null , 'cargo_list': [ { 'cargo_merchant_name': 'M. del Pont', 'cargo': [ { 'cargo_quantity': '51', 'cargo_unit': 'cj', 'cargo_commodity': 'velas' } ] }, { 'cargo_merchant_name': 'W. Paats', 'cargo': [ { 'cargo_quantity': '200', 'cargo_unit': 'cj', 'cargo_commodity': 'quesos' } ] }, { 'cargo_merchant_name': 'F F.', 'cargo': [ { 'cargo_quantity': '200', 'cargo_unit': 'cj', 'cargo_commodity': 'ginebra' } ] }, { 'cargo_merchant_name': 'F. Meyer', 'cargo': [ { 'cargo_quantity': '2', 'cargo_unit': 'casc', 'cargo_commodity': 'vino' } ] }, { 'cargo_merchant_name': 'H. Koch', 'cargo': [ { 'cargo_quantity': '58', 'cargo_unit': 'cj', 'cargo_commodity': 'manufacturas' } ] }, { 'cargo_merchant_name': 'Bemberg C.', 'cargo': [ { 'cargo_quantity': '36', 'cargo_unit': 'fds', 'cargo_commodity': 'papel' } ] }, { 'cargo_merchant_name': 'C. Riva', 'cargo': [ { 'cargo_quantity': '20', 'cargo_unit': 'btos', 'cargo_commodity': 'quesos' } ] }, { 'cargo_merchant_name': 'J. Lopez', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'cj', 'cargo_commodity': 'armas' } ] }, { 'cargo_merchant_name': 'Verney C.', 'cargo': [ { 'cargo_quantity': '23', 'cargo_unit': 'id', 'cargo_commodity': 'id' } ] }, { 'cargo_merchant_name': 'A. Bunge', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'id', 'cargo_commodity': 'vino' } ] }, { 'cargo_merchant_name': 'L. Logegaray', 'cargo': [ { 'cargo_quantity': '26', 'cargo_unit': 'id', 'cargo_commodity': 'id' }, { 'cargo_quantity': '6', 'cargo_unit': 'barriles', 'cargo_commodity': 'ferreteria' } ] }, { 'cargo_merchant_name': 'Mallman C.', 'cargo': [ { 'cargo_quantity': '8', 'cargo_unit': 'fds', 'cargo_commodity': 'lana' }, { 'cargo_quantity': '1', 'cargo_unit': 'bto', 'cargo_commodity': 'mtras' } ] }, { 'cargo_merchant_name': 'F. Chás é hijos', 'cargo': [ { 'cargo_quantity': '61', 'cargo_unit': 'id', 'cargo_commodity': 'cristaleria' } ] }, { 'cargo_merchant_name': 'C. F. Bally', 'cargo': [ { 'cargo_quantity': '30', 'cargo_unit': 'id', 'cargo_commodity': 'calzado' } ] }, { 'cargo_merchant_name': 'J. Cadmus', 'cargo': [ { 'cargo_quantity': '100000', 'cargo_unit': francos, 'cargo_commodity': 'dinero' }, { 'cargo_quantity': '15', 'cargo_unit': 'btos', 'cargo_commodity': 'papel' }, { 'cargo_quantity': '917', 'cargo_unit': null, 'cargo_commodity': 'rieles' }, { 'cargo_quantity': '679', 'cargo_unit': 'btos', 'cargo_commodity': 'fierro' } ] } ], 'passengers': null, 'in_ballast': null, 'quarantine': null, 'forced_arrival': null, 'obs': null }"
                            },
                            "EJEMPLO 4": {
                                "input":"Fecha de arribo: 1 de marzo de 1880; puerto de salida: Montevideo vapor inglés Saturno 200 tons cap Magnasco á P Risso con: á F Uriburu 1 cj mercs; S Biecker 9 barr vacios; B Iruol 1 paq pfts 120; Carlisle C 1 id encoms; F de las Carreras 1 fdo id de tránsito para el Uruguay 238 btos mercs.",
                                "output":"{ 'travel_departure_date': null, 'travel_arrival_date': '1880-03-01', 'travel_departure_port': 'Montevideo', 'travel_port_of_call_list': [], 'ship_type': 'vapor', 'ship_name': 'Saturno', 'ship_tons_capacity': 200, 'ship_tons_units': tons, 'ship_flag': 'inglés', 'master_role': 'cap', 'master_name': 'Magnasco', 'broker_name': 'P Risso' , 'cargo_list': [ { 'cargo_merchant_name': 'F Uriburu', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'cj', 'cargo_commodity': 'mercs' } ] }, { 'cargo_merchant_name': 'S Biecker', 'cargo': [ { 'cargo_quantity': '9', 'cargo_unit': 'barr', 'cargo_commodity': 'vacios' } ] }, { 'cargo_merchant_name': 'B Iruol', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'paq', 'cargo_commodity': '120 pfts' } ] }, { 'cargo_merchant_name': 'Carlisle C', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'id', 'cargo_commodity': 'encoms' } ] }, { 'cargo_merchant_name': 'F de las Carreras', 'cargo': [ { 'cargo_quantity': '1', 'cargo_unit': 'fdo', 'cargo_commodity': 'id' } ] }, { 'cargo_merchant_name': 'de tránsito para el Uruguay', 'cargo': [ { 'cargo_quantity': '238', 'cargo_unit': 'btos', 'cargo_commodity': 'mercs' } ] } ], 'passengers': null, 'in_ballast': null, 'quarantine': null, 'forced_arrival': null, 'obs': null }"
                            }
                        },
                        "field_definitions":{
                            "travel_departure_date": "La fecha en que el barco salió del puerto de origen. Esta fecha nunca puede ser posterior a \"travel_arrival_date\". En caso de estimarla, debe calcularse en relación con \"travel_arrival_date\". Si el mes de salida es mayor que el mes de arribo, la fecha de salida pertenece al año anterior.  Ejemplo: Si la fecha de arribo es el 5 de febrero de 1890 (1890-02-05) y la fecha de partida es el 30 de octubre, el mes de salida (octubre) es mayor que el mes de arribo (febrero), por lo que la fecha de partida será el 30 de octubre de 1889 (1889-10-30).",
                            "travel_arrival_date": "La fecha en que el barco llegó al puerto de destino. Se indica como 'fecha de arrobo'",
                            "travel_departure_port": "El nombre del puerto desde el cual salió el barco. Siempre es el primer puerto de salida (siempre está antecedido por \"puerto de salida: \"), los siguientes puertos de salidas, si los hay, son puertos de escala.",
                            "travel_port_of_call_list": "Lista de objetos que describen los puertos (y opcionalmente más información como fechas de llegada) en los que el barco hizo escala durante su trayecto al puerto de llegada.",
                            "ship_type": "El tipo de embarcación, e.g., barca, bergantín, bergantín goleta, fragata, goleta, lugre, polacra, vapor, zumaca. Abreviaturas comunes: [berg|berg gta|gta|vap]",
                            "ship_name": "El nombre propio del barco.",
                            "ship_tons_capacity": "El peso total o capacidad de carga del buque en toneladas.",
                            "ship_tons_units": "Especifica las unidades en las que está expresado las dimensiones del buque. Generalmente aparece en toneladas, pero puede aparecer también en quintales.  Abreviaturas comunes: [tons|ton]",
                            "ship_flag": "El país o nacionalidad, puede ser un gentilicio, bajo cuya bandera navega el barco. Ejemplo: bergantín \"francés\", vapor \"español\", polacra \"griega\", bergantin goleta paquete \"oriental\"",
                            "master_role": "El cargo de la persona responsable a bordo, e.g., capitán, patrón, piloto. Abreviaturas comunes: [cap.|c.|p.]",
                            "master_name": "El nombre de la persona responsable a bordo.",
                            "broker_name": "Nombre del agente de carga, responsable de facilitar la entrega de las mercancías transportadas. En los registros, suele ubicarse entre el nombre del capitán y el del primer destinatario de la mercancía. Normalmente está precedido por el carácter \"á\" y seguido por la expresión \"con: á\" o simplemente \"á\". Por ejemplo: \"cap Eddes á E. Norton con: á Bemberg C. 5 fds...\". En este caso, \"E. Norton\" corresponde al agente de carga.",
                            "cargo_list": "Lista de objetos que describen las mercancías y sus respectivos dueños o destinatarios. Por tanto cargo_list es una lista o array donde cada ítem debe contener el nombre del destinatario i la lista de características de sus mercancias. Las características de las mercancias deben ser la cantidad, la unidad de medida y la clase de mercancia o nombre del producto. Cada objeto en la lista debe seguir esta estructura: {'cargo_merchant_name': 'Nombre del destinatario de la carga', 'cargo': [{'cargo_quantity': 'array de números', 'cargo_unit': 'unidad (barricas|barriles|bocoys|bolsas|bordelesas|bultos|btos|cajas|cj|cjs|cascos|casc|cueros|cs|fardos|fds|kilos|latas|litros|pipas|pip|toneles)', 'cargo_commodity': 'tipo de mercancía o nombre del producto'}]}. La cantidad se expresará como una cadena de caracteres debido alos errores del OCR que a menudo confunde numeros por letras parecidas. Así podrà indicarse el valor extraido en el texto analizado con independencia de si la transcripción OCR ha sido correcta o no. Un ejemplo de cargo_list seria: [{'cargo_merchant_name':'Pedro Miralles', 'cargo':[{'cargo_quantity': 'ZO', 'cargo_unit': 'barriles', 'cargo_commodity': 'aceite' }]}, {'cargo_merchant_name':'Francisco Granado', 'cargo':[{ 'cargo_quantity': '2000', 'cargo_unit': 'kilogramos', 'cargo_commodity': 'algodón' }, { 'cargo_quantity': '20', 'cargo_unit': 'paquetes', 'cargo_commodity': 'hierro' }]}]. Cada destinatario está asociado únicamente con las mercancías listadas despuésde su nombre. El destinatario siempre aparece a la izquierda, seguido de las mercancías correspondientes a la derecha (cuando en lugar del nombre dice \"al mismo\" va el nombre del broker_name; ejemplo: \"á Caleri con: al mismo 540 pipas\" -> \"al mismo\"==\"Caleri\"). No sustituyas la palabra 'al mismo'. Por ejemplo, la expresión \"Ratto con: al mismo 12014 vino tinto, 4014 vino blanco\" debe interpretarse como: { \"cargo_merchant_name\": al mismo, \"cargo\": [ { \"cargo_quantity\": '12014', \"cargo_unit\": null, \"cargo_commodity\": \"vino tinto\" }, { \"cargo_quantity\": '4014', \"cargo_unit\": null, \"cargo_commodity\": \"vino blanco\" } ] }. Ignorar el uso de la palabra \"con\", ya que no representa un atributo de las mercancías. Si la mercancía es dinero, la cantidad debe corresponder a la moneda transportada y la mercancía debería fijarse a 'dinero', por ejemplo, la expresión 'D. J. A. Rovira: 3.000 dólares y 15 btos papel' debe interpretarse como: { 'cargo_merchant_name': 'D. J. A. Rovira', 'cargo': [ { 'cargo_quantity': 3000, 'cargo_unit': 'dólares', 'cargo_commodity': 'dinero' }, { 'cargo_quantity': 15, 'cargo_unit': 'btos', 'cargo_commodity': 'papel' }]}. Es común que se utilice las palabras 'id', 'id.' o 'idem' para referirse a la cantidad, unidad o mercancía inmediatamente anterior, evitando la repetición. Ejemplos: 'a J. Palomo 5 toneles de vino, à los Srs. Coneh y Levym 25 id id, à D. A. Casamitjana id. barriles id. y à J. M. Casamitjana id. id id'. Dicho ejemplo debería producir la salida de cargo_list sigïente:[{'cargo_merchant_name':'J. Palomo', 'cargo':[{'cargo_quantity': '5', 'cargo_unit': 'toneles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'Srs. Coneh y Levym', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'toneles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'D. A. Casamitjana', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'barriles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'J. M. Casamitjana', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'barriles', 'cargo_commodity': 'vino'}]}]. Si no coneces el valor que debe sustituir les palabras 'id', 'id. o 'idem', no inventes, deja la palabra original en su correspondiente campo. Ejemplo: 'à Cerdà 23 id id' debe resolverse como:[{'cargo_merchant_name':'R. Cerdà', 'cargo':[{'cargo_quantity': '23', 'cargo_unit': 'id', 'cargo_commodity': 'id'}]}]. Cuando la entrada especifica una cantidad y únicamente un identificador (en lugar de dos, como sería esperado para unidad y mercancía), se debe duplicar el identificador para asignarlo tanto a la unidad como a la mercancía. Ejemplo: \"Thompson 75 cjs tejidos; Stokes 9 id\" -> {\"cargo_merchant_name\": \"Thompson\", \"cargo\": [{\"cargo_quantity\": [75], \"cargo_unit\": \"cjs\", \"cargo_commodity\": \"tejidos\"}]}, {\"cargo_merchant_name\": \"Stokes\", \"cargo\": [{\"cargo_quantity\": [9], \"cargo_unit\": \"id\", \"cargo_commodity\": \"id\"}]}. Hay mercancías (cargo_commodity) que no explicitan unidades, por ejemplo 'baldosas' o 'rieles', o si existe no fueron explicitadas (ejemplo: '2945 baldosas'); en estos casos en 'cargo_unit' será 'null' y en 'cargo_commodity' va 'baldosas' o 'rieles'. Cuando la entrada NO especifica una unidad el valor por defecto es 'null' (Ejemplo: '3 btos papel à D A. Obiols, 7 rieles y 9 btos hierro à Vda. de Gracia Hernando' -> {'cargo_list':[{'cargo_merchant_name':'D. A. Obiols', 'cargo':[{'cargo_quantity': 3, 'cargo_unit': 'btos', 'cargo_commodity': 'papel' }]}, {'cargo_merchant_name':'Vda. de Gracia Hernando', 'cargo':[{ 'cargo_quantity': 7, 'cargo_unit': null, 'cargo_commodity': 'rieles' }, { 'cargo_quantity': 9, 'cargo_unit': 'btos', 'cargo_commodity': 'hierro' }]}]}. Cuando en lugar del nombre del destinatario de la mercancía se indica 'à la orden', significa que esa mercancia no tienen destinatario porque es propiedad del patrón, del capitan, del propietario o del consignatario del barco. Por elemplo ' à la orden 17 jamones'. En este ejemplo la salida sería: {'cargo_list':[{'cargo_merchant_name':'à la orden', 'cargo':[{'cargo_quantity': '17', 'cargo_unit': null, 'cargo_commodity': 'jamones' }]}]}. En algunos casos la carga las embarcaciones no son mercancias sino lastre (piedras, tierra, etc.) para poder navegar. Cuando un barco lleva lastre en lugar de mercancias se indica con la frase 'en lastre.'. La salida que debes devolver en ese caso es: {'cargo_list':[{'cargo_merchant_name':null, 'cargo':[{'cargo_quantity': null, 'cargo_unit': null, 'cargo_commodity': 'en lastre' }]}]}.",
                            "quarantine": "Información relativa a la existencia de condiciones especiales de la llegada motivadas por circunstancias sanitarias que imponen la cuarentena. Cuando esto sucede, después de describir la carga se añade la frase 'Queda en cuarentena' o 'En cuarentena'. Generalment las embarcaciones no se ponen en cuarentena, por eso en la mayoría de casos no se indicarà nada. Para normalizar la salida, exista o no la información, siempre deberás generar el atributo 'quarantine', si no aparece la informació el valor de este atributo serà 'false'; si aparece será 'true'.",
                            "forced_arrival": "Información sobre la llegada al puerto debido a causas imprevistas, como un arribo forzoso por temporal, avería u otras emergencias. Siempre deberás generar el atributo 'forced_arrival', si no aparece la informació el valor de este atributo serà 'False'; si aparece será 'True'. En caso de indicar arribo forzoso, suele describirse la carga pero no se indican los destinatarios. En su lugar se indica mediante pa preposició 'para' el puerto de destino donde se dirigía. También sule indicarse informació relativa a la declaración realizada por el responsable de la embarcació. Todo ello, al no existir campos específicos para esos datos, debería consignarse en una campo de tipo observaciones llamado 'obs'. Ejemlo: 'con 2 t. de lana para Rouan. —Ha dado declaracion á las 12 del mediodia. Viene de arribada forzosaa causa del temporal.' -> {'cargo_list':[{'cargo_merchant_name':null, 'cargo':[{'cargo_quantity': '2', 'cargo_unit': 't.', 'cargo_commodity': 'lana'}]}], 'forced_arrival':True, 'obs':'su destino era Rouan. Ha dado declaracion á las 12 del mediodia. Viene de arribada forzosaa causa del temporal.'}",
                            "obs": "Notas o comentarios adicionales que aborden aspectos no contemplados en las variables registradas, proporcionando información contextual o relevante sobre el evento."
                        }
                    },
                    "fields_to_assign":[
                        {
                            "source":"travel_departure_date",
                            "target":"travel_departure_date"
                        },
                        {
                            "source":"travel_arrival_date",
                            "target":"travel_arrival_date"
                        },
                        {
                            "source":"travel_departure_port",
                            "target":"travel_departure_port"
                        },
                        {
                            "source":"travel_port_of_call_list",
                            "target":"travel_port_of_call_list"
                        },
                        {
                            "source":"ship_type",
                            "target":"ship_type"
                        },
                        {
                            "source":"ship_name",
                            "target":"ship_name"
                        },
                        {
                            "source":"ship_tons_capacity",
                            "target":"ship_tons_capacity"
                        },
                        {
                            "source":"ship_tons_units",
                            "target":"ship_tons_units"
                        },
                        {
                            "source":"ship_flag",
                            "target":"ship_flag"
                        },
                        {
                            "source":"master_role",
                            "target":"master_role"
                        },
                        {
                            "source":"master_name",
                            "target":"master_name"
                        },
                        {
                            "source":"broker_name",
                            "target":"broker_name"
                        },
                        {
                            "source":"cargo_list",
                            "target":"cargo_list"
                        },
                        {
                            "source":"quarantine",
                            "target":"quarantine"
                        },
                        {
                            "source":"forced_arrival",
                            "target":"forced_arrival"
                        },
                        {
                            "source":"obs",
                            "target":"ai_observations"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "ReplaceIdemByValueInItemFromListCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.cargo_list",
                                "last_extracted_data.cargo_list"
                            ],
                            "key": "cargo_list"
                        }                        
                    ]
                }                
            }
        ]
    }
}
```
Ejemplo completo usando regex i openai de forma mixta:
```json
{
    "boatdata.extractor": {
        "field_version": "boat_fact-00.00.01",
        "constants": {"arrival_port": "Barcelona","news_section":"E"},
        "config": [
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 15,
                    "fields_to_extract": [
                        {
                            "temporary_field": true,
                            "default_value": "y",
                            "copy_last_value": true,
                            "key": "time_of_arrival"
                        },
                        {
                            "temporary_field": true,
                            "default_value": "mercante",
                            "copy_last_value": true,
                            "key": "purposeType"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_flag"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "TimeOfArrivalRelativeToPublicationCalculator",
                            "temporary_field": true,
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "time_of_arrival"
                        },
                        {
                            "calculator": "ElapsedTimeFromArrivalToPublicationCalculator",
                            "temporary_field": true,
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "elapsed_days_from_arrival"
                        }
                    ],
                    "main_regex": "flag"
                }
            },
            {
                "approach_type": "regex",
                "configuration": {
                    "max_groups": 10,
                    "fields_to_extract": [
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "travel_departure_port"
                        },
                        {
                            "default_value": "??",
                            "copy_last_value": false,
                            "key": "travel_duration_value"
                        },
                        {
                            "default_value": "?",
                            "copy_last_value": true,
                            "key": "travel_duration_unit"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_type"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_name"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "ship_tons_capacity"
                        },
                        {
                            "temporary_field": true,
                            "default_value": "t.",
                            "copy_last_value": false,
                            "key": "ship_tons_unit"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "master_role"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "master_name"
                        },
                        {
                            "default_value": "????",
                            "copy_last_value": false,
                            "key": "info_text",
                            "temporary_field": true
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "DataFromConstantCalculator",
                            "init_data": ["constants"],
                            "key": "news_section",
                            "literalParams": ["news_section"]
                        },
                        {
                            "calculator": "DataFromConstantCalculator",
                            "init_data": ["constants"],
                            "key": "travel_arrival_port",
                            "literalParams": ["arrival_port"]
                        },
                        {
                            "calculator": "PortOfCallsFromOriginPortCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id",
                                "extracted_data"
                            ],
                            "params": [{
                                "type": "fieldName",
                                "value": "travel_departure_port"
                            }],
                            "key": "travel_port_of_call_list"
                        },
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.travel_duration_value",
                                "last_extracted_data.travel_duration_value"
                            ],
                            "key": "travel_duration_value"
                        },
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.travel_duration_unit",
                                "last_extracted_data.travel_duration_unit"
                            ],
                            "key": "travel_duration_unit"
                        },
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.travel_departure_port",
                                "last_extracted_data.travel_departure_port"
                            ],
                            "key": "travel_departure_port"
                        },
                        {
                            "calculator": "PreviousDateFromElapsedDaysCalculator",
                            "fieldParams": [
                                "extracted_data.elapsed_days_from_arrival",
                                "extracted_data.publication_date"
                            ],
                            "key": "travel_arrival_date"
                        },
                        {
                            "calculator": "PreviousDateFromElapsedTimeCalculator",
                            "fieldParams": [
                                "extracted_data.travel_duration_value",
                                "extracted_data.travel_duration_unit",
                                "extracted_data.travel_arrival_date"
                            ],
                            "key": "travel_departure_date"
                        }
                    ],
                    "main_regex": "boat_fact"
                }
            },
            {
                "approach_type": "openai",
                "source_field": "info_text",
                "configuration": {
                    "microservice_initializer_file":"/etc/.portada_microservices/ms_init.properties",
                    "model": "gpt-4o-mini",
                    "model_config": {
                        "temperature": 0,
                        "max_tokens": 9000,
                        "top_p": 0,
                        "frequency_penalty": 0,
                        "presence_penalty": 0
                    },
                    "ai_instructions": {
                        "messages_config": {
                            "system": {
                                "role": "system",
                                "content": "Eres un asistente experto en extraer información estructurada de la carga transportada en barcos. Debes responder EXCLUSIVAMENTE con un objeto JSON válido que contenga los campos solicitados. Si no encuentras información para algún campo, debes responder con el valor null en ese campo."
                            },
                            "template": {
                                "role": "user",
                                "content": "Extrae la siguiente información de la carga transportada en barco, descrita en la nota, utilizando el formato JSON exacto: {json_template}. Aquí está la definición de cada clave: {field_definitions}. Ejemplos: {input_example}. Texto de donde extraer la información: {input_text}"
                            }
                        },
                        "json_template": {
                            "cargo_list":[],
                            "quarantine":false,
                            "forced_arrival":false,
                            "obs":null
                        },
                        "json_schema":{
                          "type": "json_schema",
                          "json_schema": {
                            "name": "more_entry_information",
                            "strict": true,
                            "schema": {
                              "type": "object",
                              "properties": {
                                "cargo_list": {
                                  "type": "array",
                                  "description": "Lista de mercancías transportadas y sus propietarios.",
                                  "nullable": true,
                                  "items": {
                                    "type": "object",
                                    "properties": {
                                      "cargo_merchant_name": {
                                        "type": "string",
                                        "description": "Es el propietario de la carga o aquella persona a quien dicha carga va destinada.",
                                        "nullable": true
                                      },
                                      "cargo": {
                                        "type": "array",
                                        "description": "Lista de mercancías transportadas.",
                                        "nullable": true,
                                        "items": {
                                          "type": "object",
                                          "properties": {
                                            "cargo_quantity": {
                                              "type": "string",
                                              "description": "Representa la cantidad total de la carga en forma numérica. Se expresa como cadena de caracteres para evitar errores en el JSON si en la cantidad figuran letras en lugar de números debido a errores tipográficos o de transcripció del OCR. Si el número no está presente, debe asignarse el símbolo ?.",
                                              "nullable": true
                                            },
                                            "cargo_unit": {
                                              "type": "string",
                                              "description": "Expresa las unidades de medida en las que la carga aparece. Ejemplo: 'cargo_unit': 'cj', 'cargo_unit':'barriles', 'cargo_unit': 'id'",
                                              "nullable": true
                                            },
                                            "cargo_commodity": {
                                              "type": "string",
                                              "description": "Expresa los distintos productos o tipos de mercancías que transporta el buque. Ejemplo: 'cargo_commodity': 'cristales', 'cargo_commodity': 'id', 'cargo_commodity': 'vino'",
                                              "nullable": true
                                            }
                                          },
                                          "required": ["cargo_quantity", "cargo_unit", "cargo_commodity"],
                                          "additionalProperties": false
                                        }
                                      }
                                    },
                                    "required": ["cargo_merchant_name", "cargo"],
                                    "additionalProperties": false
                                  }
                                },
                                "quarantine": {
                                  "type": "boolean",
                                  "description": "Información relativa a la existencia de condiciones especiales de la llegada motivadas por circunstancias sanitarias que imponen la cuarentena.",
                                  "nullable": true
                                },
                                "forced_arrival": {
                                  "type": "boolean",
                                  "description": "Información sobre la llegada al puerto debido a causas imprevistas, como un arribo forzoso por temporal, avería u otras emergencias.",
                                  "nullable": true
                                },
                                "obs": {
                                  "type": "string",
                                  "description": "Notas o comentarios adicionales que aborden aspectos no contemplados en las variables registradas, proporcionando información contextual o relevante sobre el evento.",
                                  "nullable": true
                                }
                              },
                              "required": [
                                "cargo_list",
                                "quarantine",
                                "forced_arrival",
                                "obs"
                              ],
                              "additionalProperties": false
                            }
                          }
                        },
                        "examples": {
                            "EJEMPLO 1": {
                                "input": "con 1140 fanegas trigo á D. Juan Estrany, y 9 balas papel á D. Pedro Rius.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':'1140', 'cargo_unit':'fanegas', 'cargo_commodity':'trigo'}], 'cargo_merchant_name':'D. Juan Estrany'},{'cargo':[{'cargo_quantity':'9', 'cargo_unit':'balas', 'cargo_commodity':'papel'}], 'cargo_merchant_name':'D. Pedro Rius.'}], 'quarentine':False, 'forced_arrival':False, 'obs':None}"
                            },
                            "EJEMPLO 2": {
                                "input": "con 900 sacos harina y 6 qq. carnaza á los Sres. Font y Rindor, 54 id. à don Santiago Serra y Amat, y 17 de jamones à la órden.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':'900', 'cargo_unit':'sacos', 'cargo_commodity':'harina'}, {'cargo_quantity':'6', 'cargo_unit':'qq', 'cargo_commodity':'carnaza'}], 'cargo_merchant_name':'Sres. Font y Rindor'},{'cargo':[{'cargo_quantity':'54', 'cargo_unit':'qq', 'cargo_commodity':'carnaza'}], 'cargo_merchant_name':'Santiago Serra y Amat'},{'cargo':[{'cargo_quantity':'17', 'cargo_unit':Null, 'cargo_commodity':'jamones'}], 'cargo_merchant_name':'a la orden'}], 'quarentine':False, 'forced_arrival':False, 'obs':None}"
                            },
                            "EJEMPLO 3": {
                                "input": "con 1.300 qq. azufre á don Amadeo Cros, 400 bultos espartería a don Alejo Moragull, 400 id. id. à don Antonio Puig.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':'1300', 'cargo_unit':'qq', 'cargo_commodity':'azufre'}], 'cargo_merchant_name':'don Amadeo Cros'},{'cargo':[{'cargo_quantity':'400', 'cargo_unit':'bultos', 'cargo_commodity':'esparteria'}], 'cargo_merchant_name':'don Alejo Moragull'},{'cargo':[{'cargo_quantity':'400', 'cargo_unit':bultos, 'cargo_commodity':'esparteria'}], 'cargo_merchant_name':'don Antonio Puig'}], 'quarentine':False, 'forced_arrival':False, 'obs':False}"
                            },
                            "EJEMPLO 4": {
                                "input": "con 76,000 duelas, 284 balas algodon y 100 barriles resina á don Vicente Vilaró. Queda en cuarentena.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':'76000', 'cargo_unit':None, 'cargo_commodity':'duelas'}, {'cargo_quantity':'284', 'cargo_unit':'balas', 'cargo_commodity':'algodón'}, {'cargo_quantity':'100', 'cargo_unit':'barriles', 'cargo_commodity':'resina'}], 'cargo_merchant_name':'don Vicente Vilaró'}], 'quarentine':True, 'forced_arrival':False, 'obs':None}"
                            },
                            "EJEMPLO 5": {
                                "input": "en lastre consignado á D. Pedro Olivas.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':None, 'cargo_unit':None, 'cargo_commodity':'en lastre'}], 'cargo_merchant_name':'D. Pedro Olivas'}], 'quarentine':False, 'forced_arrival':None, 'obs':None}"
                            },
                            "EJEMPLO 6": {
                                "input": "con 519 bullos vino para Rouan. —Ha dado declaracion á las siete y media de la mañana. Viene de arribada forzosa para reparar averias.",
                                "output": "{'cargo_list':[{'cargo':[{'cargo_quantity':'519', 'cargo_unit':'bullos', 'cargo_commodity':'vino'}], 'cargo_merchant_name':None}], 'quarentine':False, 'forced_arrival':True, 'obs':['Ha dado declaracion á las siete y media de la mañana', 'para Rouan']}"
                            }
                        },
                        "field_definitions":{
                            "cargo_list": "Lista de objetos que describen las mercancías y sus respectivos dueños o destinatarios. Por tanto cargo_list es una lista o array donde cada ítem debe contener el nombre del destinatario i la lista de características de sus mercancias. Las características de las mercancias deben ser la cantidad, la unidad de medida y la clase de mercancia. Cada objeto en la lista debe seguir esta estructura: {'cargo_merchant_name': 'Nombre del destinatario de la carga', 'cargo': [{'cargo_quantity': 'array de números', 'cargo_unit': 'unidad (barricas|barriles|bocoys|bolsas|bordelesas|bultos|btos|cajas|cj|cjs|cascos|casc|cueros|cs|fardos|fds|kilos|latas|litros|pipas|pip|toneles)', 'cargo_commodity': 'tipo de mercancía'}]}. La cantidad se expresará como una cadena de caracteres debido alos errores del OCR que a menudo confunde numeros por letras parecidas. Así podrà indicarse el valor extraido en el texto analizado con independencia de si la transcripción OCR ha sido correcta o no. Un ejemplo de cargo_list seria: [{'cargo_merchant_name':'Pedro Miralles', 'cargo':[{'cargo_quantity': 20, 'cargo_unit': 'barriles', 'cargo_commodity': 'aceite' }]}, {'cargo_merchant_name':'Francisco Granado', 'cargo':[{ 'cargo_quantity': '2000', 'cargo_unit': 'kilogramos', 'cargo_commodity': 'algodón' }, { 'cargo_quantity': '20', 'cargo_unit': 'paquetes', 'cargo_commodity': 'hierro' }]}]. Cada destinatario está asociado únicamente con las mercancías listadas inmediatamente antes de su nombre. El destinatario siempre aparece a la derecha. Si la mercancía es dinero, la cantidad debe corresponder a la moneda transportada y la mercancía debería fijarse a 'dinero', por ejemplo, la expresión '3.000 dólares y 15 btos papel à D. J. A. Rovira' debe interpretarse como: { 'cargo_merchant_name': 'D. J. A. Rovira', 'cargo': [ { 'cargo_quantity': 3000, 'cargo_unit': 'dólares', 'cargo_commodity': 'dinero' }, { 'cargo_quantity': 15, 'cargo_unit': 'btos', 'cargo_commodity': 'papel' }]}. Es común que se utilice las palabras 'id', 'id.' o 'idem' para referirse a la cantidad, unidad o mercancía inmediatamente anterior, evitando la repetición. Ejemplos: '5 toneles de vino a J. Palomo, 25 id id à los Srs. Coneh y Levym, id. barriles id. à D. A. Casamitjana y id. id id à J. M. Casamitjana'. Dicho ejemplo debería producir la salida de cargo_list sigïente:[{'cargo_merchant_name':'J. Palomo', 'cargo':[{'cargo_quantity': '5', 'cargo_unit': 'toneles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'Srs. Coneh y Levym', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'toneles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'D. A. Casamitjana', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'barriles', 'cargo_commodity': 'vino'}]},{'cargo_merchant_name':'J. M. Casamitjana', 'cargo':[{'cargo_quantity': '25', 'cargo_unit': 'barriles', 'cargo_commodity': 'vino'}]}]. Si no coneces el valor que debe sustituir les palabras 'id', 'id. o 'idem', no inventes, deja la palabra original en su correspondiente campo. Ejemplo: '23 id id à R. Cerdà' debe resolverse como:[{'cargo_merchant_name':'R. Cerdà', 'cargo':[{'cargo_quantity': '23', 'cargo_unit': 'id', 'cargo_commodity': 'id'}]}]. Hay mercancías (cargo_commodity) que no explicitan unidades, por ejemplo 'baldosas' o 'rieles', o si existe no fueron explicitadas (ejemplo: '2945 baldosas'); en estos casos en 'cargo_unit' será 'null' y en 'cargo_commodity' va 'baldosas' o 'rieles'. Cuando la entrada NO especifica una unidad el valor por defecto es 'null' (Ejemplo: '3 btos papel à D A. Obiols, 7 rieles y 9 btos hierro à Vda. de Gracia Hernando' -> {'cargo_list':[{'cargo_merchant_name':'D. A. Obiols', 'cargo':[{'cargo_quantity': 3, 'cargo_unit': 'btos', 'cargo_commodity': 'papel' }]}, {'cargo_merchant_name':'Vda. de Gracia Hernando', 'cargo':[{ 'cargo_quantity': 7, 'cargo_unit': null, 'cargo_commodity': 'rieles' }, { 'cargo_quantity': 9, 'cargo_unit': 'btos', 'cargo_commodity': 'hierro' }]}]}. Cuando en lugar del nombre del destinatario de la mercancía se indica 'à la orden', significa que esa mercancia no tienen destinatario porque es propiedad del patrón, del capitan o del propietario del barco. Por elemplo 'con 17 jamones à la orden'. En este ejemplo la salida sería: {'cargo_list':[{'cargo_merchant_name':'à la orden', 'cargo':[{'cargo_quantity': '17', 'cargo_unit': null, 'cargo_commodity': 'jamones' }]}]}. En algunos casos la carga las embarcaciones no son mercancias sino lastre (piedras, tierra, etc.) para poder navegar. Cuando un barco lleva lastre en lugar de mercancias se indica con la frase 'en lastre.'. La salida que debes devolver en ese caso es: {'cargo_list':[{'cargo_merchant_name':null, 'cargo':[{'cargo_quantity': null, 'cargo_unit': null, 'cargo_commodity': 'en lastre' }]}]}. En algunos casos pudiera ser que el lastre tenga un dueño o consignatario al que se deberá entregar. Este tipo de textos tienen la forma siguiente: 'en lastre á los senores Serra Y Parladé.'. la salida de este tipo de entrada serà: {'cargo_list':[{'cargo_merchant_name':'senores Serra Y Parladé', 'cargo':[{'cargo_quantity': null, 'cargo_unit': null, 'cargo_commodity': 'en lastre' }]}]}.",
                            "quarantine": "Información relativa a la existencia de condiciones especiales de la llegada motivadas por circunstancias sanitarias que imponen la cuarentena. Cuando esto sucede, después de describir la carga se añade la frase 'Queda en cuarentena' o 'En cuarentena'. Generalment las embarcaciones no se ponen en cuarentena, por eso en la mayoría de casos no se indicarà nada. Para normalizar la salida, exista o no la información, siempre deberás generar el atributo 'quarantine', si no aparece la informació el valor de este atributo serà 'false'; si aparece será 'true'.",
                            "forced_arrival": "Información sobre la llegada al puerto debido a causas imprevistas, como un arribo forzoso por temporal, avería u otras emergencias. Siempre deberás generar el atributo 'forced_arrival', si no aparece la informació el valor de este atributo serà 'False'; si aparece será 'True'. En caso de indicar arribo forzoso, suele describirse la carga pero no se indican los destinatarios. En su lugar se indica mediante pa preposició 'para' el puerto de destino donde se dirigía. También sule indicarse informació relativa a la declaración realizada por el responsable de la embarcació. Todo ello, al no existir campos específicos para esos datos, debería consignarse en una campo de tipo observaciones llamado 'obs'. Ejemlo: 'con 2 t. de lana para Rouan. —Ha dado declaracion á las 12 del mediodia. Viene de arribada forzosaa causa del temporal.' -> {'cargo_list':[{'cargo_merchant_name':null, 'cargo':[{'cargo_quantity': '2', 'cargo_unit': 't.', 'cargo_commodity': 'lana'}]}], 'forced_arrival':True, 'obs':'su destino era Rouan. Ha dado declaracion á las 12 del mediodia. Viene de arribada forzosaa causa del temporal.'}",
                            "obs": "Notas o comentarios adicionales que aborden aspectos no contemplados en las variables registradas, proporcionando información contextual o relevante sobre el evento."
                        }
                    },
                    "fields_to_assign":[
                        {
                            "source":"cargo_list",
                            "target":"cargo_list"
                        },
                        {
                            "source":"quarantine",
                            "target":"quarantine"
                        },
                        {
                            "source":"forced_arrival",
                            "target":"forced_arrival"
                        },
                        {
                            "source":"obs",
                            "target":"ai_observations"
                        }
                    ],
                    "fields_to_calculate": [
                        {
                            "calculator": "ReplaceIdemByValueInItemFromListCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.cargo_list",
                                "last_extracted_data.cargo_list"
                            ],
                            "key": "cargo_list"
                        }                        
                    ]
                }                
            }
        ]
    }
}
```

# Preparación de la configuración 

Para empezar a configurar los extractores de los diferentes periódicos del _Proyecto PorTAda_ será necesario, o bien, bajarse la aplicación _autoNewsExtractorDev_ en el enlace [_autoNewsExtractorDev.zip_](https://drive.google.com/file/d/1UBCOwoWMHVPY9bpfrQbXnQQh5WSmgjz4/view?usp=drive_link) y descomprimir el archivo, o bien, clonar el repositorio [jportada_boat_fact_extractor](https://github.com/portada-git/jportada_boat_fact_extractor).  Es posible que no hayáis de implementar código alguno. En ese caso, la opción preferida debería ser  la descarga e instalación de la aplicación compilada. Sin embargo, en el caso de que la información contenida en vuestros periódicos requiera algún tipo de cálculo en alguno de vuestros campos a extraer, la mejor opción, entonces, sería la clonación del repositorio para poder añadir el código de vuestros calculadores.  De momento podéis empezar con la descarga de la aplicación y en caso de que necesitéis codificar alguna cosa, ya realizaréis la clonación a posteriori. 

## Instalación de _autoNewsExtractorDev_

 Para instalar la aplicación, una vez descargada desde el enlace [_autoNewsExtractorDev.zip_](https://drive.google.com/file/d/1UBCOwoWMHVPY9bpfrQbXnQQh5WSmgjz4/view?usp=drive_link) solamente se debe descomprimir el archivo descargado.  Esto creará el directorio "_run_autonewsextractor_dev_", dentro del cual se encontrara el archivo ejecutable (_boat_fact_extractor.jar_) y 10 scripts (5 para ejecutar bajo Windows y 5 bajo Linux/MAC) que ayudaran a realizar y probar la configuración que debéis realizar. 

Una vez descomprimido el archivo _autoNewsExtractorDev.zip_ y comprobado su contenido, será necesario configurar los directorios de configuración. Para facilitar esta tarea y evitar errores, se ha creado un repositorio en _Github_ llamado [ _portada_boat_fact_extractor_config_data_](https://github.com/portada-git/portada_boat_fact_extractor_config_data) en el que se han definido los directorios básicos y los principales ficheros a usar para cada uno de los equipos del proyecto. Se ha usado un repositorio de github con los directorios y ficheros porque la configuración final de cada equipo debe subirse al servidor del proyecto.

Así pues, deberéis clonar el repositorio _portada_boat_fact_extractor_config_data_ en vuestro ordenador local. Una vez clonado, moved y renombrad el repositorio local (recién clonado), con el nombre _config_, al directorio de ejecución del programa _autoNewsExtractorDev_ y que si no habéis renombrado, debería ser _run_autonewsextractor_dev_. El resultado de esta operación debería ser el que se muestra en la siguiente imagen:

![Repositorio de configuración dentro del directorio de ejecución de autoNewsExtractorDev](media/directorisExecucio.png)

Aseguraros que el directorio _config_ es vuestro repositorio local de _portada_boat_fact_extractor_config_data_, ya que así, se podrá sincronizar fácilmente y sin peligro los cambios que los diferentes equipos vayan realizando. 

# La aplicación _autoNewsExtractorDev_

La aplicación _autoNewsExtractorDev_ no tiene versión gráfica. Debe usarse desde la consola del sistema ejecutando cada un de los scripts, o directamente el ejecutable si la extensión _jar _ la tenéis asociada a la máquina virtual JAVA. El .jar esta compilado para ser ejecutado por la versión 11 o superior de la máquina virtual. Si disponéis de una máquina virtual de inferior versión actualizadla.

Los scripts que encontraréis en el directorio de instalación (_run_autonewsextractor_dev_) de la aplicación son:
 - *BoatFactInfoUnitJoinTest.run* / *BoatFactInfoUnitJoinTest.bat*. Este script permite configurar y testear la funcionalidad de "ensamblaje de los archivos digitales de una misma unidad informativa". Es necesario indicarle donde se encuentra el fichero de configuración (init.properties), el directorio con las fuentes de texto y el directorio donde se escribirán los nuevos ficheros ensamblados.  Para hacer el test se necesitan diversos archivos de varias unidades informativas, algunas de ellas compuestas por más de un archivo.
 - *BoatFactCutterTest.run* / *BoatFactCutterTest.bat*. Este script se puede usar para configurar y testear la funcionalidad de "recorte de los fragmentos-objetivo". Para probar será necesario configurar una expresión regular para detectar el inicio del fragmento y otra para detectar el final. Además, se necesitarán archivos de texto ya ensamblados conteniendo el fragmento-objetivo (las entradas de barcos y manifiestos) además de otros textos. Necesita que se le indique donde se encuentra el fichero de configuración, el directorio con los ficheros fuente y el directorio donde guardar los fragmentos segregados. Este proceso es independiente del anterior. Pueden usarse archivos arreglados manualmente o los devueltos por la funcionalidad de ensamblaje. 
 - *BoatFactExtractTest.run* / *BoatFactExtractTest,bat*. Este script está preparado para probar la extracción de datos de ficheros de texto con el contenido de las noticias de entradas de barcos y manifiestos. Para ello deberán configurarse las expresiones regulares pertinentes y el archivo JSON que lo gestiona. Se le deberá indicar donde se encuentra el fichero de configuración, el directorio con los ficheros fuente y el nombre base (sin extensión) del fichero donde escribirá los datos extraídos en un formato  JSON.
 - *BoatFactExtract.run* / *BoatFactExtract.bat*. Una vez probada cada una de las funcionalidades por separado, mediante este script es posible integrarlas todas ellas en un solo proceso. Requiere la indicación de la ubicación del fichero de configuración, el directorio fuente y el nombre base del fichero donde escribir la lista de resultados. 
 -  *BoatFactExtractorCommand.run* / *BoatFactExtractorCommand.bat*. Este es un script genérico que mediante un argumento extra permite ejecutar los  4 procesos anteriores. El argumento extra debe posicionarse en primer lugar y debe tener alguno de los siguientes valores: 'information_unit_test', 'cut_test', 'extract_test' o 'extract', Inmediatamente después del comando deberán especificarse los mismos argumentos usados para las diferentes funcionalidades según sea el caso.
 
 Finalmente, si la extensión '_.jar_' se encuentra asociada a la máquina virtual _java_, debería poder usarse directamente el ejecutable (_boat_fact_extractor.jar_) pasándole los mismos argumentos que los pasados al script anterior.

Los archivos de texto para realizar las pruebas deberán contener las noticias procesadas de manera que cada párrafo se encuentre escrito en una única línea. Los párrafos, títulos, cabeceras, números de página, etc. se encontrarán separados por un único salto de línea. 

## Configuración y prueba de la utilidad _BoatFactInfoUnitJoinTest_

Esta utilidad requiere de configuración muy simple y un banco de pruebas relativamente pequeño. No precisa de expresión regular alguna y al existir un único enfoque solo será necesario comprobar que el fichero "init.properties" contenga los siguientes atributos y valores:
 - **information_unit_builder_proxy_packages_to_search**=org.elsquatrecaps.autonewsextractor.informationunitbuilder.reader
 - **file_extension**=txt
 - **informationUnitBuilderType**=file_name
 - **metadataSource**=portada_file_name

En el directorio fuente colocar ficheros de texto con nombres que sigan el patrón definido en el apartado [Ensamblador de archivos digitales](#ensamblador-de-archivos-digitales). Es decir: AAAA_MM_DD_PUE_NP_E_PG_BLOC.txt. Con independencia del contenido, asegurad que disponéis de una variedad de nombres suficiente para probar las distintas posibilidades.

Argumentos de la ejecución:

 - **-c**: indicará el nombre y ubicación del fichero de configuración inicial. Por  ejemplo: `-c config/conf_db/init.properties`
 - **-d**: debe contener la ruta del directorio donde se encuentran los ficheros de texto a tratar. Ejemplo: `-d data_db`
 - **-o**: indica la ruta del directorio de salida donde se desea escribir los ficheros resultantes. Los ficheros de la entrada que no respondan al patrón esperado no se copiaran a la salida. Los ficheros con la misma fecha, periódico y edición, pero con distintas páginas o bloques, se unirán en uno solo con el nombre del fichero de página y bloque inferior, seguido del sufijo "__informationUnit_". Si no hay dos o más ficheros coincidentes, pero cumple el patrón esperado, se copiará al directorio de salida añadiendo el mismo sufijo. 
 
Si en el directorio de entrada tenemos los ficheros: 
 - 1852_01_01_BCN_DB_U_16_0001.txt
 - 1852_01_02_BCN_DB_U_06_0001.txt
 - 1852_01_02_BCN_DB_U_07_0001.txt
 - 1852_01_02_BCN_DB_U_07_0002.txt
 - aaaaa.txt

Al ejecutar esta utilidad en el directorio de salida obtendríamos los ficheros:

 - 1852_01_01_BCN_DB_U_16_001_informationUnit.txt
 - 1852_01_02_BCN_DB_U_06_001_informationUnit.txt

Ejemplo de ejecución:

`$ ./BoatFactInfoUnitJoinTest.run -c config/conf_db/init.properties -d text_db -o resultats/iu`

## Configuración y prueba de la utilidad _BoatFactCutterTest_

Esta utilidad necesita crear al menos dos ficheros con expresiones regulares. Dependiendo de los periódicos  se podrán necesitar 4. El objetivo de estas expresiones regulares consiste en detectar cuál es el inicio y el final del fragmento-objetivo de manera que se pueda dividir todo el texto de un periódico a tratar, aislando el fragmento de interés y eliminando el resto. 

Una expresión regular debe detectar el inicio del fragmento. Con ello se eliminará todo el texto desde el comienzo hasta donde se ha detectado la parte inicial del fragmento. 

Una segunda expresión regular,  detectará donde puede acabar el texto y eliminará el texto que abarque desde el elemento detectado hasta el final de todo el texto.

Así, el fragmento resultante será exclusivamente el fragmento de interés.

Los ficheros conteniendo las expresiones regulares se ubicarán como parte del sistema _regex_ y seguirán la lógica descrita en el apartado [Conjunto de expresiones regulares](#conjunto-de-expresiones-regulares).  

### Detector del inicio del fragmento

Deberá responder al nombre de "fragment_initial_detector" y al ser la expresión generadora necesitará de la extensión .regex, con la expresión deseada, y también la extensión .options, con las opciones de procesamiento activas. Esta expresión deberá dividir el texto del fichero en  3 grupos:
 1. El primer grupo contendría el texto desde el inicio hasta justo antes, donde empieza el fragmento de interés.
 2. El segundo grupo contendrá una parte del texto de interés usada para detectar el inicio del fragmento, por ejemplo el título de la sección, algún subtítulo, etc.
 3. El tercer grupo contendrá el texto que vaya desde el final del fragmento de detección hasta el final del fichero.
 
 Veamos un ejemplo. En el Diario de Barcelona, en general, la sección relativa a las embarcaciones entradas se encuentra bastante bien señalada. Muchas veces encontramos la lista de entradas bajo el título y subtítulo:
 
	SANIDAD DEL PUERTO
	Embarcaciones llegadas a puerto [DIA_DE_LLEDADA_RELATIVO] 

Un rápido vistazo a las imágenes y sus transcripciones nos permite ver que la frase "Embarcaciones llegadas ...", se encuentra, normalmente, escrita en cursiva. La mayoría de  procesadores OCR presentan una menor calidad con las letras cursivas, por lo que usar solamente el subtítulo no nos parece buena idea. Por contra, la calidad de las letras mayúsculas suele ser algo mayor que las minúsculas. Así pues decidimos usar el título como discriminador.  Dicho título no nos resulta útil durante la extracción, por lo que lo ubicaremos dentro del primer grupo (el que se debe descartar). En cambio, tanto la referencia a las embarcaciones llegadas en el día de ayer|hoy|anteayer|..., sí nos resulta útil durante la extracción, para poder calcular la fecha de llegada, ya que este dato no aparece explícitamente en la noticia. Deberemos, por tanto, ubicarlo en el segundo grupo. En el tercer grupo ubicaremos el resto del texto hasta el final del archivo. Veamos.

Una noticia tipo sería:

	PARTE ECONOMICA.
	AVISOS CASAS DE HUÉSPEDES.
	...
	ABERTURAS DE REGISTRO.
	Para Tarragona, Coruña y Santander. Saldrá de este puerto a la mayor brevedad posible el bergantin español Firme, forrado en cobre, su capitan D. Santiago Matossi; admite carga á flete para dichos puntos. Lo despachan los Sres. Salazar y Torrents, pórtico Xifré, escritorio рітстран
	Para Cádiz y escalas. El vapor español Barcino saldrá el 10 del corriente, á las nueve de la mañana: admitiendo cargo y pasajeros. Se despacha en la calle de la Merced, esquina á la plaza de S. Sebastian, número 46, nuevo, cuarto principal.
	Para Génova y Liorna. Saldrá de este puerto la polacra toscana Calidoro, su capitan D. José Tonietti; para cuyos puntos admite carga á flete y pasajeros. Se despacha en la calle de Abaixadors, núm. 10, cuarto.
	SANIDAD DEL PUERTO.
	Embarcaciones llegadas al puerto en el dia de ayer.
	Mercantes españolas.
	De Christiansund en 33 d. bergantin Fama, de 109 t., c. D. V. Ramon Rodriguez, con 5930 vogs bacalao y 200 de pezpalo á la órden.
	De Almería y Aguilas en 15 d. laud Aguila, de 35 t., p. S. Lopez, con 130 gq. perdigon es á D. A. Sala, 50 id. á D. J. Margarit. 400 de plomo á D. J. Serratosa, 200 fanegas cebada á Don B. Solá y Amat, y 12 millares esparto á D. S. Garriga.
	...
	Mercante francesa.
	De Marsella en 21 horas vapor Elba, de 210 t., c. S. Gabriel , con 69,000 francos á los señores Vidal y Cuadras hermanos, 83,000 id. á los señores Girona hermanos, Clavé y compañía , 23,000 id. D. J. M. Serra, 21,900 id. á los señores Serra y Parladé, 13.000 id. á D. B. Roca y Cortada, 15.000 id. á los señores Staguo, Torrens y compañia, 1500 id. á D. 1. Domenech, 3 cajas sangnijuclas á don B. Solá y Amat, otros efertos para esta, y 103 baltos de varios géneros de tránsito y 30 pasajeros, consignado á los señores Martorell y Bosill.
	Despachadas el 30 de diciembre.
	Bergantin español Wifredo, c. D. J. Ferrer, para Valparaiso con vino, pimenton y bacalao. ...

Nuestra propuesta de expresión regular inicial sería:
```
^(.*?\nSANIDAD DEL PUERTO)\n(.*?)\n(.*)$
```
Es decir, Todo el texto desde el inicio hasta 'SANIDAD DEL PUERTO' cuando esta frase se encuentra en mayúsculas después de un salto de línea (ya que es un título), se encierra en un primer grupo. La siguiente línea (correspondiente al subtítulo) la capturaremos como grupo 2, y el resto de texto hasta el final del texto, será capturado como grupo 3.

Para que la expresión regular no se analice línea a línea, será necesario indicarlo con las opciones  `gsuU` (análisis global -g-, considerando todo el texto como un todo -s- y forzando la aceptación de caracteres unicode).

Al probar esta expresión nos damos cuenta de que, el título, que en las imágenes se encuentra centrado, a veces debido a la transparencia, en las transcripciones pueden aparecer cierto ruido a izquierda y derecha justo antes y después de los saltos de línea. También vemos que, a veces, en el título faltan letras o están mal transcritas. Y por último, nos damos cuenta de que, en ocasiones, el subtítulo, se transcribe en la misma línea que el título. Decidimos cambiar la expresión por: `^(.*?{##sanidad_del_puerto##})(.*?)\n(.*)$` donde *sanidad_del_puerto* se va a sustituir por: `\n[\{| ]{0,3}[S5].{3,5}[DO0][A4][DO0] ?[DO0]E[Ll\[\|] ?.{3,5}[RP][TY][O0]\W*\s*`

Con ello reducimos la detección del título a la mínima expresión reconocible, además añadimos caracteres ruido a izquierda y derecha. El funcionamiento ahora es mucho más eficiente. 

Antes de dar por terminado el detector inicial, observamos que en algunos períodos, el título SANIDAD DEL PUERTO, desaparece de la sección y solo podemos reconocer "_ Embarcaciones llegadas ..._". Decidimos mantener la expresión encontrada, pero añadir una alternativa con el subtítulo. De esta forma, donde exista el título, se aplicará el discriminador primero y donde no exista el alternativo.

La expresión final que resulta eficiente en prácticamente todos los casos probados, es:
```
^(.*?{##sanidad_del_puerto##})(.*?)\n(.*)$
^(.*?\n)((?:[\{| ]{0,3}(?:{##embarcaciones##})\s+(?:(?:{##llegadas##})|(?:.*{##puerto##}))\s+[^\n]*)\s?{##mercantes##} *\w{3,}[s5]?[\W\s]+)(.*)$
```
Para sortear las posibles trascripciones de baja calidad debido a la letra cursiva, en lugar de forzar toda la frase literal, la reducimos, simplificando su contenido, pero forzando que la frase candidata vaya seguida de una palabra similar a _mercantes_. Podéis consultar en el directorio _regex_ los ficheros con los valores de sustitución.

Es importante fijarse que cuando usamos alternativas en la misma expresión principal que generará toda la expresión final, debemos asegurarnos que cada alternativa contenga exactamente los 3 grupos, ya que si en una de ellas pusiéramos menos (o más) grupos de los previstos, la detección no funcionaria.

### Detector del final del fragmento
En este detector se procesa solamente el texto obtenido en el grupo 3 de la fase anterior, la de detección del inicio del fragmento. Es decir, el que incluye parte del texto de interés junto con el resto del texto existente entre las embarcaciones llegadas y el final del ejemplar analizado.

En este caso, la expresión regular dividirá el texto analizado en dos grupos. En el grupo 1 quedará el fragmento con el texto de las embarcaciones entradas (que deberá mantenerse) y en el grupo 2, el texto restante (que deberá ser eliminado).

La lógica de construcción de la expresión, es similar a la anterior y se define mediante el mecanismo de composición de la expresión *regex* descrito en el apartado [Conjunto de expresiones regulares](#conjunto-de-expresiones-regulares).  

El nombre del fichero contendor de la expresión principal también tiene un nombre fijo: _fragment_end_detector_ y siguendo las consideraciones _regex_ de nuestra aplicación deberá haber dos archivos con el mismo nombre (con la extensión _.regex_ y con la extensión _.options_). En este caso las opciones también deberán tratar el texto como un todo y el fichero de options contendrá `gsuU`.

Un estudio preliminar de una muestra de ejemplares nos indica que la lista de embarcaciones llegadas se acaba a menudo, cuando se inicia la siguiente sección y, por tanto, aparece un título en mayúsculas. Sin embargo, hay excepciones que, por su importante número, deberemos considerar. A veces, la lista acaba en la misma sección de SANIDAD DEL PUERTO,  pero haciendo referencia  a las embarcaciones despachadas en un día concreto. La frase que suele comenzar el bloque de embarcaciones despachadas es "Despachadas el [DIA_Y_MES]". Sin embargo, en ocasiones  puede poner "el buque ... despachado el ...". Por contra, existen también, no pocos casos en los que no aparece la información de  los buques despachados. En la mayoría de estos casos, la lista termina al iniciar otra sección con un título en mayúsculas, pero existe un número reducido en el que la sección correspondiente a "Correo de Madrid...", recibido o emitido por el gobierno, se encuentra transcrito en minúsculas.

Con todo, decidimos aplicar una expresión con múltiples alternativas, en esta ocasión aplicamos una técnica diferente que nos evita la repetición de grupos en cada alternativa. La técnica usada consiste separar las alternativas en un fichero de sustitución de manera que el _regex_ principal contenga una única línea (alternativa única). Veamos:

```
(^.*?)({##end_detector_body##}\W*\n.*+$)
```
Usando esta técnica, las alternativas situadas en el fichero _end_detector_body_ quedan dentro del paréntesis del grupo y no es necesario definir los grupos en cada alternativa.

El contenido del fichero _end_detector_body_ sería:
```
(?:\s+D[eo][sS5g?][pq].{2,3}h.d.[sS5g?]? .{1,3} {##ocr_digit_no_blanc##}{1,2} .*)
(?:\s+{##boat_fact_vessel##} d[eo][sS5g?][pq].{2,3}h.d.[sS5g?]? .{1,3} {##ocr_digit_no_blanc##}{1,2} .*)
(?:\s+C[eao](?:(?:rr)|(?:m))[aoe][oeo] de Ma.{2,5}d d.. d.a {##ocr_digit_no_blanc##}{1,2} d. .* d. {##ocr_digit_no_blanc##}{2,4})
(?:\s+[A-Z ]{3,})
```
Las 4 alternativas comentadas anteriormente, y probadas para que resulten el máximo de flexibles y eficientes, a fin de que coja prácticamente todos los casos si equivocación.  

### Ejecución y prueba de la utilidad 

Una vez creados los ficheros para la composición de  las expresiones regulares de detección del inicio u el final de fragmento-objetivo, debemos probar su funcionamiento con la ejecución de la utilidad _BoatFactCutterTest_. Esta utilidad, además de los ficheros del sistema _regex_ necesitará también del fichero de configuración inicial (_init.properties_) y de un conjunto de argumentos mínimos que se le pasarán al script _BoatFactCutterTest.[run|bat]_ desde la consola.

Los argumentos necesarios serán:
- **-c**: (configuración). Este parámetro indicará el nombre y ubicación del fichero de configuración inicial. Por ejemplo: `-c config/conf_db/init.properties`
- **-d**: (directorio de datos). Es el parámetro que debe contener la ruta del directorio donde se encuentran los ficheros de texto a tratar. Ejemplo: `-d data_db`
- **-o**: (output). Indica la ruta del directorio de salida donde se desea escribir los ficheros con los fragmentos segregados resultantes de cada fichero leído desde el directorio de datos.

Para esta utilidad, el fichero de inicialización debe contener al menos los siguientes atributos y valores:
- **target_fragment_breaker_proxy_packages_to_search**=org.elsquatrecaps.autonewsextractor.targetfragmentbreaker.cutter (lista de paquetes donde buscar los diferentes enfoques de este tipo de classes).
- **file_extension**=txt
- **fragment_breaker_approach**=regex
- **regexBasePath**=config/regex
- **fact_model**=boatfacts (debe aparecer como directorio del sistema _regex_  justo por debajo de la raíz (_regexBasepath_).
- **newspaper**=lp ( o db, o sm, o dm, ..., representa el identificador del periódico y debe aparecer como directorio del sistema _regex_  en el siguiente nivel que el _fact_model_ - segundo nivel de profundidad desde la raíz _regex_).
- **parse_model**=[extractor]  (este valor debe coincidir con un directorio de los componentes _regex_, un nivel por debajo de _newspaper_. Puede contener múltiples valores separados por coma y representan los diferentes modelos de extracción, según el tipo de noticia a tratar. Por ejemplo, los periódicos con manifiestos de  descargas y relación de embarcaciones entradas, deberían disponer de dos modelos, ya que los datos extraídos en cada caso son diferentes. En esta utilidad este dato puede usarse para albergar distintos segregadores para cada modelo).
- **ocr_engine_model**=documentAI  (este valor es opcional y puede o no aparecer como directorio del sistema _regex_. En el caso de existir un directorio auxiliar con este nombre en cualquier nivel de los directorios _regex_ tendría por objetivo de este ofrecer una opción alternativa a una expresión regular dada debido a la idiosincrasia específica en la transcripción de un motor OCR concreto). 

Ejemplo de ejecución:

`$ ./_BoatFactCutterTest.run -c config/conf_db/init.properties -d text_db -o resultats/cu`

Por cada fichero de entrada, esta utilidad producirá tantos ficheros como ítems tenga el parámetro _parse_model_, ya que se da por supuesto que en un mismo periódico los fragmentos correspondientes a distintos tipos de noticias estarán ubicados en  lugares distintos y, por tanto, tendrán detectores de inicio y final diferentes. Para distinguirlos, los ficheros de salida tomarán el nombre original al que añadirán un sufijo formado por el nombre del parse_model precedido del guion-subrayado (_). Por ejemplo, si `parse_model=[entradas,manifiestos]`, el tratamiento de un fichero llamado `1852_01_02_BCN_DB_U_07_0002.txt` daría como resultado los siguientes archivos:
 - `1852_01_02_BCN_DB_U_07_0002_entradas.txt`
 - `1852_01_02_BCN_DB_U_07_0002_manifiestos.txt`

## Configuración y prueba de la utilidad _BoatFactExtractTest_

Esta es la utilidad que requiere más configuración. Por un lado, el fichero de configuración inicial también será necesario aquí. Para el enfoque  basado en expresiones regulares, será necesario adaptar las expresiones a la extracción a realizar, teniendo en cuenta el sistema _regex_ de composición de expresiones complejas ya explicado (ver el apartado [Composición de expresiones regulares complejas](#composici%C3%B3n-de-expresiones-regulares-complejas)). Además, la configuración precisará también de un fichero JSON que especifique como se debe procesar la extracción, cuantos niveles jerárquicos debe tener, qué campos querremos extraer y que cálculos serán necesarios, para transformar los datos obtenidos, a los datos que finalmente guardaremos. 

### Datos previos a la extracción
Los datos extraídos del nombre del fichero hacen referencia a información relativa a la publicación (fecha, identificador del periódico, edición y páginas), se encuentran siempre disponibles con datos extraídos, ya que se procesan como datos por defecto. Por tanto, si fuera necesario se podrían usar para calcular otro valores.

### Modelo de datos y verificación de versiones
Uno de los aspectos más críticos en un proyecto como PorTAda, es el modelo de datos y su integridad,  tanto por la cantidad campos, como por la evolución que pueden sufrir a medida que el proyecto vaya avanzando. Los ficheros de configuración especifican los nombres de los campos y sus características. Un error de transcripción en el nombre de un campo o un desfase en las versiones usadas, podrían implicar problemas posteriores a la hora de integrar todos los datos extraídos.

Para intentar reducir el problema, tanto los datos extraídos como las  configuraciones dispondrán  de un identificador de versiones. En los datos, el identificador, pude permitir hacer cambios automáticos de versiones, evitando tener que repetir procesos. En los ficheros de configuración, el identificador de versiones permitirá verificar que no se encuentra desfasado y que no contiene errores de transcripción de los nombres de campos.

La aplicación _[jportada_boat_fact_extractor](https://github.com/portada-git/jportada_boat_fact_extractor)_ verificará siempre los ficheros de configuración de los extractores de datos antes de iniciar el proceso. En caso de encontrar un desfase o un nombre de campo erróneo, interrumpirá el proceso e informará con un mensaje en la consola  indicando la razón del problema. Además, la aplicación dispone de una opción para mostrar, de forma dinámica, la información de la última versión. 

Se puede consultar la información relativa a los campos en la misma aplicación _autoNewsExtractorDev_ usando el script genérico `BoatFactExtractorCommand.[run|bat]` con los argumentos _field_info_ e _-i_ con una combinación cualquiera de las letras VDCA. V indica que queremos ver el nombre de la versión actual, D, la descripción de cada campo, C los cambios sufridos en los nombres de campos en las diferentes versiones y A sería equivalente a poner las 3 letras DCV. Por ejemplo, si ejecutamos:

```
BoatFactExtractorCommand.run field_info -i DV

```

obtendremos:

```
                 FIELD INFO                      
======================================================================
CURRENT VERSION: boat_fact-00.00.00
----------------------------------------------------------------------
======================================================================
 List of fildes and desciption for the current version
======================================================================
CURRENT NAME FIELD                 FIELD DESCRIPTION                  
----------------------------------------------------------------------
model_version:    Indicates the version of the field name model.
----------------------------------------------------------------------
publication_date:    Displays the date of the newspaper
----------------------------------------------------------------------
publication_name:    Displays the name of the newspaper
----------------------------------------------------------------------
publication_edition:    Indicates the edition of the newspaper in case there is more than one per day: M for morning, T for afternoon or N for evening. In case there is only one edition, the value will be U (unique).
----------------------------------------------------------------------
fact_type:    This is the type of news analyzed. It can take values ​​such as E for ship entrances or M for discharge manifests.
----------------------------------------------------------------------
ship_departure_port:    Indicates the port of departure of the ship in this travel
----------------------------------------------------------------------
ship_arrival_port:    Indicates the port of arrival (Marseille, Buenos Aires, Havana or Barcelona) of the ship in this travel. In most cases, this information does not appear in the news and is implicitly deduced depending on the newspaper
----------------------------------------------------------------------
ship_departure_date:    It denotes the ship’s departure date from the departure port
----------------------------------------------------------------------
ship_arrival_date:    Indicates the date that the ship arrived in the arrival port (Marseille, Buenos Aires, Havana or Barcelona)
----------------------------------------------------------------------
travel_arrival_moment_value:    Indicates the time of arrival at port. It can be expressed as the time of arrival or as a broader period (morning, afternoon, evening, ...)
----------------------------------------------------------------------
ship_travel_time:    Indicates the time that the ship was travelling from the departure port to the arrival port days or hours
----------------------------------------------------------------------
ship_travel_time_unit:    Indicates the unit of time in which the duration is expressed.
----------------------------------------------------------------------
ship_port_of_call_list:    Indicates the list of ports (and optionally more information as arrival or departure dates) that the ship had stopped while on her way to the arrival port. If the information of this list is only the name of ports, the list will be compounded by port names separated by commas
----------------------------------------------------------------------
ship_port_of_call_place:    Show the name of one item of the port of call list
----------------------------------------------------------------------
ship_port_of_call_arrival_date:    Show the arrival date of one item of the port of call list
----------------------------------------------------------------------
ship_port_of_call_departure_date:    Show the departure date of one item of the port of call list
----------------------------------------------------------------------
ship_type:    Describes the type of the ship (brick, brick-goelette, trois-mats, vapeur etc) that the newspaper mention
----------------------------------------------------------------------
ship_flag:    Refers to the name of the country or region of the flag of the ship describe by the newspaper
----------------------------------------------------------------------
ship_name:    Indicates the name of the ship typically presented in full, like is mention in the newspaper source
----------------------------------------------------------------------
ship_tons:    Specifies the ship’s capacity in tons presented as a numerical value with the unit of measurement. In the case of the ships this remains always the same as it refers to the tonnage of the ship. This data is given usually with abbreviations such as "ton." or "t."
----------------------------------------------------------------------
ship_master_role:    It refers to the category of the person who commands the ship. It can be a captain or a skipper, although in a few cases a pilot also appears. The abbreviations used to designate them are usually “c” and “p”, respectively
----------------------------------------------------------------------
ship_master_name:    It is the nominal identification of the person who commands the ship. It can appear in various ways, at least it has the surname, preceded by his position (role). Lists the surname of the ship's captain, often preceded by "cap." or "c."
----------------------------------------------------------------------
ship_agent:    This information could indicate either the ship agent, namely the person that is responsible for the transactions and the operation of the ship or the shipowner, namely the person that owns the ship or part of the ship. Sometimes it can also refers to shipowner
----------------------------------------------------------------------
ship_crew:    It is the numerical value of the ship's crew.
----------------------------------------------------------------------
ship_cargo_list:    It is the description of the list with the information related to all the cargo transported by the incoming vessel (type of cargo, quantity, person receiving of the cargo, if any or "to order" otherwise, etc.)
----------------------------------------------------------------------
cargo_merchant:    It is the person to whom the cargo was destined, often it will be the merchant who had bought it and who took charge of it at the time of unloading. Indicates the recipient of the cargo, with occasional mention of "divers" [various/several].
In this case we see names of people or companies. These names have the same characteristics and difficulties as the rest of the names. Sometimes the ships arrived in full loads and were destined for the same person, and in other cases, each load had its recipient. The expression “a la orden” also appears frequently, which in principle is a load to be sold upon arrival at the port and which, on the contrary, does not have a previous owner, beyond the captain himself personally or on behalf of someone.
----------------------------------------------------------------------
cargo_type:    It expresses the products or types of goods that have arrived. It is a very variable value, the most common goods are coal or cotton, but there is an extraordinary diversity of products that arrive at the port.
----------------------------------------------------------------------
cargo_value:    Numerical expression of the amount of charge
----------------------------------------------------------------------
cargo_unit:    Expresses the units in which the load appears. These may be units of weight, volume, counts, or units related to packaging.
----------------------------------------------------------------------
cargo_origin:    Port of origin of the cargo
----------------------------------------------------------------------
cargo_destination:    Port of destination of the cargo
----------------------------------------------------------------------
ship_quarantine:    Information relative to special conditions of the arrival motivated by sanitary circumstances.
----------------------------------------------------------------------
ship_forced_arrival:    Indication about the causes of the forced arrival
----------------------------------------------------------------------
ship_amount:    This field appears only in quantitative models where, instead of specifying the information for each ship, the number of vessels that have arrived or are about to arrive is indicated. Normally, it is a model specifically intended for cabotage transport.
----------------------------------------------------------------------
ship_origin_area:    This field appears only in quantitative models where, instead of specifying information about each ship, the area of ​​origin or transport is used. Normally, it is a model specifically intended for cabotage transport.

```

La información relativa a los cambios de versiones de muestra indicando el nombre actual, a la izquierda y el historial de cambios sufridos (a la derecha). El esquema usado es:

```
 List of changes made in each field throughout the different versions 
======================================================================
CURRENT NAME FIELD         <=         PREVIOUS NAME FIELDS            
----------------------------------------------------------------------
current_name_c1   <=  name_c1_version_1 <= name_c1_version_0
current_name_c2 
current_name_c3
...
current_name_cn  <= name_cn_version_0
```

### Uso de campos temporales y cálculo de campos definitivos

Existe la posibilidad que algunos campos no aparezcan directamente en las noticias a extraer, pero pueda deducirse a partir de algún otro.  Por ejemplo, en el Diario de Barcelona, no se indica nunca la fecha de llegada. Sin embargo, sí que se explicita una relación temporal de la llegada, relativa a la fecha de publicación. Ejemplo:

_Embarcaciones llegadas el día de **ayer**
..._

El encabezamiento de la sección nos permite deducir la fecha de llegada, a partir de la fecha de la publicación y de la información relativa al momento de la llegada respecto a publicación ( ayer, hoy, anteayer, etc.).  

También pude ocurrir que necesitemos un campo temporal para almacenar un cálculo intermedio. Por ejemplo, continuando con el ejemplo anterior, se puede decidir generar otro campo temporal con el valor de los días pasados desde la llegada de la embarcación hasta la fecha en que se publica la llegada. Esto es, si el título indica anteayer, habrán pasado 2 días. Si indica ayer, solo 1 día y si indicara hoy, 0 días. Con este dato, calculado, sería muy fácil obtener la fecha real de llegada. 

Para tratar estos caso, necesitaremos extraer una información de forma temporal y aplicar un cierto cálculo, almacenar el cálculo como valor temporal y usarlo, finalmente, para deducir la fecha. La información extraída ("_momento relativo de la llegada_") deberá almacenarse con los datos extraídos para poder ser usada por el calculador específico. De forma parecida, los días pasados desde la llegada a hasta el día de la publicación también deberá almacenarse como información calculada.  Esto implica que deberemos asignar un nombre a cada dato en el fichero JSON. Al ser nombres de campos temporales no referenciados en el modelo de datos, la verificación del fichero fallaría si no se indicara explícitamente que se trata de valores temporales.  La verificación no comprueba los campos temporales. Se puede explicitar que un campo es temporal en la especificación del campo, ya sea de la sección de campos a extraer o ya sea en la sección de campos a calcular.  Siguiendo con el ejemplo del Diario de Barcelona:

```json
{
    "boatdata.extractor": {
       ...
        "config": [
            {
                ...
                "configuration": {                   
                    "fields_to_extract": [
                        {
		                        "key": "time_of_arrival",
                            "temporary_field": true
                        },
                        ...
                    ],
                    "fields_to_calculate": [
                        {
                            "key": "elapsed_days_from_arrival",
                            "temporary_field": true,
                            "calculator": "ElapsedTimeFromArrivalToPublicationCalculator",
                            "fieldParams": ["extracted_data.time_of_arrival"],
                        }
                       ...
                    ],
                    ...
                }
            },
            ...
        ],
        ...
   }
}
```

### Calculadores existentes
Tanto en la biblioteca *[jportada_auto_news_extractor_lib](https://github.com/portada-git/jportada_auto_news_extractor_lib)*, como la aplicación  _[jportada_boat_fact_extractor](https://github.com/portada-git/jportada_boat_fact_extractor)_ tienen ya implementados un conjunto de calculadores se pueden especificar, sin más, en el fichero de configuración. Veamos los calculadores existentes:

 - *DataFromConstantCalculator*: Este calculador devuelve el valor de la constante indicada en los parámetros de entrada. Requiere estar inicializado con el conjunto de valores constantes definidos en el archivo de configuración JSON (*extractor_config.json*). <br>Veamos un ejemplo, en un *parser_model* llamado extractor, se define una constante llamada *arrival_port*. Posteriormente, en la sección *configuration* de uno de sus extractores se especifica como uno de los campos a calcular (*fields_to_calculate*) el calculador  *DataFromConstantCalculator* la inicialización del cual (*init_data*) se debe realizar con las constantes definidas. Además, se le pasa como parámetro el nombre de la constante deseada como un dato literal ("*arrival_port*"). El valor devuelto por el calculador se asignará al campo llamado *ship_arrival_port*.
 ```json
{
    "extractor": {
        "field_version": "boat_fact-00.00.00",
        "constants": {"arrival_port": "Barcelona"},
        ...
        "config":[
            ...
            {
                ...
                "configuration":{
                    ...
                    "fields_to_calculate": [
                        ...
                        {
                            "calculator": "DataFromConstantCalculator",
                            "init_data": ["constants"],
                            "literalParams": ["arrival_port"],
                            "key": "ship_arrival_port"
                         }
                         ...
                    ]
                    ...
                }
                ...
            }
            ...
        ]
        ...
    }
    ...
}
 ```
 
 <dl><dd>
En este ejemplo, al campo *arrival_port* se le asignará el valor calculado "Barcelona".
 </dd></dl>
 
 - *DataFromConstantMapAndConfigKeyCalculator*: Este calculador es parecido al anterior, pero es específico para manejar constantes con valores compuestos. Recibe dos parámetros, el nombre de la constante con valores compuestos y el nombre del campo de los datos compuestos requerido para dvolver su valor. <br>Veamos un ejemplo, en un *parser_model* llamado extractor, se define una constante llamada *port_candidates* de tipo compuesto, con cuatro campos. Posteriormente, en la sección *configuration* de uno de sus extractores se especifica como uno de los campos a calcular (*fields_to_calculate*) el calculador  *DataFromConstantMapAndConfigKeyCalculator* la inicialización del cual (*init_data*) se debe realizar con las constantes definidas. Además, se le pasa como parámetro el nombre de la constante deseada como un dato literal ("*port_candidates*") y el nombre del campo extraído o calculado con anterioridad, del cual obtener el valor del segundo parámetro. El valor devuelto por el calculador se asignará al campo llamado *ship_arrival_port*.
```json
{
    "extractor": {
        "field_version": "boat_fact-00.00.00",
        "constants": {
            "arrival_port": "Barcelona",
            "port_candidates":{
                "BCN":"Barcelona",
                "BUE": "Buenos Aires",
                "HAV":"La Habana",
                "MAR":"Marseille"
            }
        },
        ...
        "config":[
            ...
            {
                ...
                "configuration":{
                    ...
                    "fields_to_calculate": [
                        ...
                        {
                            "calculator": "DataFromConstantMapAndConfigKeyCalculator",
                            "init_data": ["constants"],
                            "literalParams": ["port_candidates"],
                            "field_params":["news_port"],
                            "key": "ship_arrival_port"
                         }
                         ...
                    ]
                    ...
                }
                ...
            }
            ...
        ]
        ...
    }
    ...
}
```
 
 <dl><dd>
En este ejemplo, al campo *arrival_port* se le asignará uno de los posibles valores dependiendo del valor encontrado en el campo *news_port*.
 </dd></dl>
 
 - *ReplaceIdemByValueCalculator*: Este calculador recibe 2 parámetros. El primero contiene el valor que se quiere analizar y el segundo el valor de sustitución en caso de que el valor de primer parámetro contenga un valor similar a "idem" o equivalente. Si el valor a chequear no coincide con "idem", devuelve su valor, pero si hay coincidencia, el valor devuelto es el del segundo parámetro.<br>En el siguiente ejemplo, se configura uno de los campos a calcular *ship_travel_time_unit*, usando el calculador *ReplaceIdemByValueCalculator*. Esta se inicializa con la configuración ("init_properties") y con el parser_id usado durante el proceso de extracción y cálculo. Además, recibe el valor del campo *ship_travel_time_unit* recién extraído, así como el valor que tuvo la última entrada extraída de forma completa. 
```json
{
    "extractor": {
        "field_version": "boat_fact-00.00.00",
        ...
        "config":[
            ...
            {
                ...
                "configuration":{
                    ...
                    "fields_to_calculate": [
                        ...
                        {
                            "calculator": "ReplaceIdemByValueCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": [
                                "extracted_data.ship_travel_time_unit",
                                "last_extracted_data.ship_travel_time_unit"
                            ],
                            "key": "ship_travel_time_unit"
                         }
                         ...
                    ]
                    ...
                }
                ...
            }
            ...
        ]
        ...
    }
    ...
}
```
 
 <dl><dd>
Si el valor de  *ship_travel_time_unit* recién extraído es equivalente a "idem", se le asignará el valor de la última entrada. En caso contrario, se dejará con el valor original.
 </dd></dl>
 
 - *TimeOfArrivalRelativeToPublicationCalculator*: Este calculador analiza un texto el cual contenga "*hoy*", "*ayer*", "*anteayer*" o equivalentes y devuelve un identificador unívoco para cada uno de ellos. Con una palabra equivalente a ayer devolverá "y" correspondiente al concepto "yesterday", con una equivalente a anteayer devolverá "b" correspondiente a "before yesterday", etc. Este calculador requiere inicializarse con la configuración (init.properties) y el parser_id a procesar. Recibe un único parámetro con el texto conteniendo hoy, ayer, anteayer, etc.<br>Vemos un ejemplo en el  que se quiere cambiar  el valor extraído como  *time_of_arrival* reemplazándolo por su identificador temporal según su contenido. 
```json
{
    "extractor": {
        "field_version": "boat_fact-00.00.00",
        ...
        "config":[
            ...
            {
                ...
                "configuration":{
                    ...
                    "fields_to_calculate": [
                        ...
                        {
                            "calculator": "TimeOfArrivalRelativeToPublicationCalculator",
                            "init_data": [
                                "configuration",
                                "parser_id"
                            ],
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "time_of_arrival"
                            "temporary_field": true,
                         }
                         ...
                    ]
                    ...
                }
                ...
            }
            ...
        ]
        ...
    }
    ...
}
```
 
 - *ElapsedTimeFromArrivalToPublicationCalculator*: Calcula el número de días transcurridos en función del identificador de un valor temporal relativo (ayer, hoy, anteayer). No necesita datos iniciales y solo recibe, como único parámetro, el identificador del valor temporal.
```json
{
                        ...
                        {
                            "calculator": "ElapsedTimeFromArrivalToPublicationCalculator",
                            "temporary_field": true,
                            "fieldParams": ["extracted_data.time_of_arrival"],
                            "key": "elapsed_days_from_arrival"
                        }
                         ...
```
 
 - *PreviousDateFromElapsedTimeCalculator*: Este calculador no necesita datos iniciales. Su objetivo es calcular una fecha previa a partir de valor numérico de tiempo expresado en días o en horas y una fecha concreta pasada como cadena de caracteres en un formato definido. El calculador recibe 4 parámetros: 
	 - Un valor numérico que indica el tiempo transcurrido
	 - Un valor indicando la unidad de tiempo. Si comienza por *h* se consideran horas, si lo hace por *d* se consideran días. 
	 - La fecha a partir de la que se debe hacer el cálculo en un formato específico como cadena de caracteres.
	 - El formato con el que la fecha se expresa. Este parámetro es opcional. Si el formato de la fecha es yyyy-MM-dd, no es necesario este parámetro. En caso contrario debe especificarse el formato. Ejemplo:
```json
{
                        ...
                        {
                            "calculator": "PreviousDateFromElapsedTimeCalculator",
                            "fieldParams": [
                                "extracted_data.ship_travel_time",
                                "extracted_data.ship_travel_time_unit",
                                "extracted_data.ship_arrival_date"
                            ],
                            "literalParams":["dd-MM-yyyy"],                            
                            "key": "ship_departure_date"
                        }
                         ...
```
 - *PreviousDateFromElapsedTimeCalculator*: Este calculador no necesita datos iniciales. Su objetivo es calcular una fecha previa a partir de valor numérico de tiempo expresado en días o en horas y una fecha concreta pasada como cadena de caracteres en un formato definido. El calculador recibe 4 parámetros: 
	 - Un valor numérico que indica el tiempo transcurrido
	 - Un valor indicando la unidad de tiempo. Si comienza por *h* se consideran horas, si lo hace por *d* se consideran días. 
	 - La fecha a partir de la que se debe hacer el cálculo en un formato específico como cadena de caracteres.
	 - El formato con el que la fecha se expresa. Este parámetro es opcional. Si el formato de la fecha es yyyy-MM-dd, no es necesario este parámetro. En caso contrario debe especificarse el formato. Ejemplo:
```json
{
                        ...
                        {
                            "calculator": "PreviousDateFromElapsedTimeCalculator",
                            "fieldParams": [
                                "extracted_data.ship_travel_time",
                                "extracted_data.ship_travel_time_unit",
                                "extracted_data.ship_arrival_date"
                            ],
                            "literalParams":["dd-MM-yyyy"],                            
                            "key": "ship_departure_date"
                        }
                         ...
```
 - *ReplaceIdemByValueInItemFromListCalculator*: Este calculador es específico para sustituir los pronombres "idem" del campo cargo_list cuando se extrae mediante openAI. Este extractor devuelve la lista entera de la carga, no ítem a ítem sino la lista completa con todos los ítems extraídos.  Por ello el reemplazador básico de las palabras "idem" (_ReplaceIdemByValueCalculator_) no funcionaría. _ReplaceIdemByValueInItemFromListCalculator_ recibe el nombre del campo donde se encuentra la lista recién extraída y con esta, itera por toda la lista en busca de los campos internos susceptibles de tener _idem_. Cuando los encuentra los sustituye por el valor del ítem anterior. Como datos de inicialización requiere la configuración y el parser_id. Como parámetros, recibe dos nombres de campo: el que contienen la lista de la carga recién extraída  y el que contiene la última lista extraída. Este segundo campo se necesita para poder hacer la sustitución en caso de que la lista actual comience directamente con un "idem". Vemos un ejemplo:
```json
{
    ...
    {
        "calculator": "ReplaceIdemByValueInItemFromListCalculator",
        "init_data": [
            "configuration",
            "parser_id"
        ],
        "fieldParams": [
            "extracted_data.cargo_list",
            "last_extracted_data.cargo_list"
        ],
        "key": "cargo_list"
    }
    ...
```
  - _MsCallerCalculator_: Esta clase no es propiamente un calculador, sino que su función es enlazar la aplicación con otro calculador vía llamada a un microservicio. Esto permite crear calculadores externos a la aplicación, los cuales podrán ser llamados por esta a través de este calculador. El calculador externo puede encontrarse tanto en el servidor de microservicios de portada, como en cualquier otro servidor. Los calculadores externos reciben, por POST, un objeto json con un único campo llamado "_parameters_by_position_" conteniendo un array de los parámetros que necesitará. La respuesta esperada por _MsCallerCalculator_ es un objeto json con dos campos. El campo _status_ es numérico e indica si la llamada y el proceso han tenido éxito. Un proceso exitoso devuelve el valor 0 para el campo _status_. Cualquier valor de _status_ diferente de 0 significará que se ha producido un error durante el proceso de llamada. Si el proceso tiene exito (_status=0_), el objeto json contendrá el campo _value_ con la respuesta (cálculo) procesada por el calculador externo. Dicha respuesta será el valor devuelto por _MsCallerCalculator_, lo que se usará para modificar el valor del campo destino indicado en la configuración del _parser_. En caso de error (_status != 0_), el segundo campo se debe llamar _message_ y debe contener una explicación textual del error. Dicho mensaje será almacenado por _MsCallerCalculator_ en un fichero de registro( _log_). La respuesta de _MsCallerCalculator_ con _status_ distinto de 0 será un valor _null_, lo que impide la asignación del valor al campo destino.<br>La configuración del parser debe contener unos campos especiales (especificados como item del array init_data) para inicializarlo, además del nombre de este calculador, los parámetros que el calculador externo debe recibir (siguiendo la sintaxis del resto de calculadores) i el nombre del campo destino. Los campos especiales de inicialización permitirán generar la llamada al microservicio donde el calculador esté ubicado. Si se encuentra en el servidor de PorTADa, será suficiente indicar el contexto (_context_) y el nombre del punto de entrada (_entry_point_). En el servidor de portada existen 4 contextos (_'python'_, _'java'_, '_r_' y '_docker_'),  Si el microservicio se encuentra fuera del servidor de portada, deberán especificarse 4 campos: protocol, host, port y pref, además del correspondiente nombre de entrada (_entry_point_). Dichos campos especiales inializaran el calculador permitiendo generar la URL de llamada como: _protocol://host:port/pref/entry_point_). 

Una posible configuración para este calculador podría ser:
``` json
{
    ...
    {
        "calculator": "MsCallerCalculator",
	"init_data":[{
        	"context": "python",
        	"entry_point":"get_date_from_publication_date_and_day_value"
	}],
        "params": [{
		        "type":"fieldValue",
		        "value":"extracted_data.publication_date",
		        "definition": "field name containing the publication date of the newspaper."
	      },{
				    "type":"fieldValue",
				    "value":"extracted_data.entry_day",
				    "description": "day of month referred to the entry day for a travel"
        }],
        "key": "cargo_list"
    }
    ...
    {
        "calculator": "MsCallerCalculator",
	"init_data":[{
        	"protocol":"https",
		"host":"site.of.this.calculator.com",
		"port":"5271",
		"pref":"calculators",
        	"entry_point":"get_duration_trip_value"
	}],
        "params": [{
		        "type":"fieldValue",
		        "value":"extracted_data.publication_date",
		        "definition": "field name containing the publication date of the newspaper."
	      },{
				    "type":"fieldValue",
				    "value":"extracted_data.entry_day",
				    "description": "day of month referred to the entry day for a travel"
        }],
        "key": "cargo_list"
    }
    ...
}
```

En el código de los microservicios de Portada debería haber una entrada 
```python
@app.route("/get_date_from_publication_date_and_day_value", methods=['POST'])  
def get_date_from_publication_date_and_day_value():  
    jsonp = request.get_json()  
    params = jsonp["parameters_by_position"]  
    pub_date = params[0]  
    day_for_date = params[1]  
    ...
    try:
	    new_date = compose_date_as(day_for_date, month, year)
	    ret = {'status'=0, 'value'=new_date)
	  except:
		  ret = {'status'=-1, 'message'='Error...')
    return jsonify(ret)
```
Y en el servidor site.of.this.calculator.com, la entrada podría ser:
```python
@app.route("calculators/get_duration_trip_value", methods=['POST'])  
def get_duration_trip_value():  
    jsonp = request.get_json()  
    params = jsonp["parameters_by_position"]  
    departure_date = params[0]  
    arrival_date = params[1]  
    ...
    try:
	    days = days_form_date_to_date(departure_date, arrival_date)
	    ret = {'status'=0, 'value'=days)
	  except:
		  ret = {'status'=-1, 'message'='Error...')
    return jsonify(ret)
```

Podéis consultar  más información sobre los calculadores en los apartados [Sistema del proxy para las utilidades FieldCalculator](#sistema-del-proxy-para-las-utilidades-fieldcalculator) y [Configuración de cada nivel de extracción](#configuraci%C3%B3n-de-cada-nivel-de-extracci%C3%B3n).

### Creación de nuevos calculadores
Es posible que al especificar algún extractor, necesitéis usar un tipo de cálculo todavía no implementado. Si eso ocurre, actualmente, la manera más fácil de hacerlo, es clonar el repositorio de esta aplicación codificada en JAVA desde _[jportada_boat_fact_extractor](https://github.com/portada-git/jportada_boat_fact_extractor)_ y crear una nueva clase en el paquete  "org.elsquatrecaps.autonewsextractor.dataextractor.calculators" con un nombre significativo que informe de su función. La clase debe heredar de AbstractCalculator o de RegexCalculator en función de si necesita usar alguna expresión regular compuesta con el sistema _regex_ (herencia de RegexCalculator) o no (herencia de AbstractCalculator).  La clase debe estar anotada por DataExtractorCalculatorMarkerAnnotation con un identificador único que permita distinguirlo de los demás. Si lo hacéis así, solamente deberéis implementar un único método llamado *calculate*. La mejor solución para evitar problemas de tipo y debido a que todos los campos extraídos, por defecto, son cadenas de carácter, es devolver siempre el valor en tipo texto. Para los parámetros, esperar un array de String es también una solución correcta. Podréis acceder a los datos iniciales especificados en el *extractor_config* usando el metodo `getInitData`al cual se le pase por parámetro en nombre de los datos de inicialización que encontraréis defindos en ExtraDataCalculatorEnum. Por ejemplo, si extractor_config ha especificado para este calculador la necesidad de pasar las constantes, obtendréis el valor de todas las constantes llamando a:
`JSONObject constantes = getInitData(ExtraDataCalculatorEnum.CONSTANTS.toString());`

Veamos a continuación como deberemos usar las anotaciones y la herencia en una clase nueva:

```java
@DataExtractorCalculatorMarkerAnnotation(id = "NewCalculator")
public class NewCalculator extends AbstractCalculator<String[], String>{
    public static final int PARAM_1=0;    
    public static final int PARAM_2=1;
    //...
    //public static final int PARAM_N=???;
    
    @Override
    public String calculate(String[] params){
        String response = "";
        //Ejemplo de obtención de la cosntantes
        JSONObject constantes = getInitData(ExtraDataCalculatorEnum.CONSTANTS.toString());
        //Codificar aquí el cálculo
        
        return response;
    }		
}
```
En el caso de que sea necesaria la implementación de calculadores, deberéis subir los cambios al repositorio para poderlo integrar todo. Mientras no se integre, podéis generar una compilación local y usar vuestro código local.

### Análisis inicial del texto
Otro aspecto importante que debemos tener en cuenta antes de comenzar a especificar la configuración del extractor, consiste en analizar el patrón de texto usado en las noticias.  Las primeras características a analizar son las jerarquías del texto y sus patrones, la repetición de los mismos, la información heredada y la información implícita.

La información implícita se refiere a la información que no aparece en ninguna parte de la noticia, pero que debemos suministrar al modelo de datos. Por ejemplo, generalmente el puerto de llegada no suele aparecer como dato, pero necesitaos especificarlo, ya en el proyecto se trabaja con varios. La información implícita la añadiremos en forma de constante y usaremos el calculador "*DataFromConstantCalculator*" o "*DataFromConstantMapAndConfigKeyCalculator*" para asignar este valor al campo deseado.

Para analizar las jerarquías, revisar el apartado [Relación jerárquica del contenido](#relaci%C3%B3n-jer%C3%A1rquica-del-contenido). Es necesario que detectemos, además de la relación de jerarquía, si esa estructura jerárquica se repite varias veces a lo largo de la sección o solo aparece una sola vez al inicio. Por ejemplo, en el Diario de Barcelona se dan los dos casos. En el inicio de la sección se informa del momento de la llegada. Pongamos por caso: "Embarcaciones llegadas anteayer". Esta información aparece únicamente una vez. Sin embargo, se informa de la bandera mediante un subtítulo y se repite varias veces para los barcos entrados de diferentes nacionalidades. Debajo de la bandera se van repitiendo las entradas de cada embarcación siguiendo un formato bien definido. Así pues, dispondremos de tres niveles jerárquicos, de las cuales el primero no se repite nunca. Esta característica nos permitirá usar solamente 2 extractores jerárquicos en lugar de 3 (revisad los apartados [Funcionamiento del extractor basado en expresiones regulares](#funcionamiento-del-extractor-basado-en-expresiones-regulares) y [Copia de datos en el mismo nivel](#copia-de-datos-en-el-mismo-nivel).

### Metodología de ensayo y error

La complejidad de la configuración, la variabilidad en la redacción a lo largo del tiempo y las diferentes calidades  de texto obtenido de las transcripciones OCR, hacen muy aconsejable plantearse una metodología incremental y basada en el ensayo y error. 

Por incremental, debemos entender se comienza con la mínima configuración (extracción de un único campo). Para ello se configura el fichero _init.properties, el JSON de extracción y se compone una expresión regular adaptada al patrón de la noticia, usando el sistema propio de la aplicación. Se va mejorando la expresión a base de ensayo y error con múltiples pruebas que abarquen una diversidad representativa del conjunto de noticias  hasta conseguir una calidad de extracción aceptable. Una vez conseguida, incrementaremos la extracción con dos campos y repetiremos el proceso de mejora. Uno a uno incrementaremos los campos a extraer hasta conseguir la extracción de todos los campos.

Para obtener la máxima información mientras se va implementando la configuración definitiva, podéis usar el atributo `run_for_debugging=yes`. Esta opción muestra por la consola las expresiones regulares usadas durante el proceso de extracción ("*Pattren (from regex_name)*"), así como el texto crudo ("*Raw text*") al que se ha procesado la búsqueda con la expresión regular, el fragmento  coincidente ("*Parsed text*"), el texto no coincidente que se reserva para el siguiente nivel de extracción ("*Unparsed text*") y los datos extraídos del fragmento coincidente ("*Extracted data*"). Ejemplo de salida durante una extracción con el atributo run_for_debugging activo:

```
Pattern (from flag): "(?:(?:^(.*(?:(?:E[mn]b.*[eo][s5])|(?:[EA][mn].{3,5}c[i¡Il1][oec]n[eosc]s)|(?:[EA]{2,3}barca.{2,4}nes)|(?:.{1,3}barc.{1,2}c[i¡Il1][oec]n[eosc].)|(?:.mbar.{1,3}c[i¡Il1][oec]n[eosc].)) (?:(?:(?:(?:[|i¡l][|i¡l])|(?:[UHN]))[eoa]g[aoeu]d..)|(?:.{4,6}adas)) .{2,7} p[uo][eo]rt[oe].*)\n+((?:(?:(?:(?:[MmNn]|(?:[ÚU]l?))[eco*][rft](?:(?:[ce][an][bnu][tl][eco*])|(?:ca[nbu][lt][lt]-)))[s5;}]?)|(?:M.r.ant[eoa][s5]?)|(?:.{1,3}rcant[aeo][s5]?)|(?:D. g[uo][aeo](?:(?:[rn][rn])|(?:m))[aeo])|(?:))) (.*)\.?$)|(?:^( )?((?:(?:(?:(?:[MmNn]|(?:[ÚU]l?))[eco*][rft](?:(?:[ce][an][bnu][tl][eco*])|(?:ca[nbu][lt][lt]-)))[s5;}]?)|(?:M.r.ant[eoa][s5]?)|(?:.{1,3}rcant[aeo][s5]?)|(?:D. g[uo][aeo](?:(?:[rn][rn])|(?:m))[aeo])|(?:))) (.*)\.?\n+)|(?:^( )?([iIl1][dD].{0,2}) ?(.{4,20})\.?\n+(?=De))|(?:^( )?([iIl1][dD].{0,2}) (.{4,15})\.?\n+)|(?:^( )?( )?([^\d\W]{5,15})\.?\n+))"

--------------

Raw text: "Embarcaciones llegadas al puerto en el dia de ayer.
Mercantes españolas.
De Christiansund en 33 d. bergantin F'ama, de 109 t., c. D. V. Ramon Rodriguez, con 5930 vog. bacalao y 200 de pezpalo á la orden. 
De Almería y Aguilas en 15 d. laud Aguila, de 35 t., p. S. Lopez, con 130 gq. perdigon es á D. A. Sala, 50 id. á D. J. Margarit. 400 de plomo á D. J. Serratosa, 200 fanegas cebada á Don B. Solá y Amat, y 12 millares esparto á D. S. Garriga."

--------------

Parsed text: "Embarcaciones llegadas al puerto en el dia de ayer.
Mercantes españolas."

--------------

Unparsed text: "De Christiansund en 33 d. bergantin F'ama, de 109 t., c. D. V. Ramon Rodriguez, con 5930 vog. bacalao y 200 de pezpalo á la orden. 
De Almería y Aguilas en 15 d. laud Aguila, de 35 t., p. S. Lopez, con 130 gq. perdigon es á D. A. Sala, 50 id. á D. J. Margarit. 400 de plomo á D. J. Serratosa, 200 fanegas cebada á Don B. Solá y Amat, y 12 millares esparto á D. S. Garriga."

--------------

Extracted data:
	 -Original field values:
		 --time_of_arrival: Embarcaciones llegadas al puerto en el dia de ayer.
		 --purposeType: Mercantes
		 --ship_flag: españolas.
	 -Calculated field values:
		 --time_of_arrival: y
		 --elapsed_days_from_arrival: 1



--------------

Parsed text: "Id. danesa."

--------------

Unparsed text: "De Calmau y Elseneur en 40 d. bergantin Terpsicore, de 132, t. c. P. N. Thave, con 286 docenas tablones de pino y 8 piezas arboladura á los Sres. Ortembach y C."

--------------

Extracted data:
	 -Original field values:
		 --time_of_arrival: 
		 --purposeType: Id.
		 --ship_flag: danesa.
	 -Calculated field values:
		 --time_of_arrival: y
		 --elapsed_days_from_arrival: 1



--------------

Parsed text: "Mercante francesa."

--------------

Unparsed text: "De Marsella en 21 horas vapor Elba, de 210 t., c. S. Gabriel , con 69,000 francos á los señores Vidal y Cuadras hermanos, 83,000 id. á los señores Girona hermanos, Clavé y compañía , 23,000 id. D. J. M. Serra, 21,900 id. á los señores Serra y Parladé, 13.000 id. á D. B. Roca y Cortada, 15.000 id. á los señores Staguo, Torrens y compañia, 1500 id. á D. 1. Domenech, 3 cajas sangnijuclas á don B. Solá y Amat, otros efertos para esta, y 103 baltos de varios géneros de tránsito y 30 pasajeros, consignado á los señores Martorell y Bosill."

--------------

Extracted data:
	 -Original field values:
		 --time_of_arrival: 
		 --purposeType: Mercante
		 --ship_flag: francesa.
	 -Calculated field values:
		 --time_of_arrival: y
		 --elapsed_days_from_arrival: 1

```

### Expresiones regulares reutilizables como componentes
Antes de entrar en el detalle del uso de las diferentes expresiones componentes, debemos insistir que la mayoría de las expresiones reusables no sirven para detectar su cometido de forma aislada, sino que cumplen su misión en combinación con el resto de la expresión regular, la cual, en su conjunto se convierte en un patrón fuerte que evita errores de detección. El uso de expresiones largas nos permite definir patrones fuertes, pero a la vez flexibles, de manera que la detección y extracción de partes del texto pueda ser muy eficiente aun con OCR de calidad baja.

En general, diremos que una expresión como las que tenemos en el sistema _regex_ necesitan muletas a ambos lados para llevar a cabo su cometido. Por ejemplo, una expresión como *ocr_alfa_number* que permite detectar números escritos en letra, presenta la forma:
```regex
[UuDdTtCcSsOoNnQqVv](?:[^\d\W]{1,18})(?: +\w +[UuDdTtCcSsOoNnQqVv][^\d\W]{1,9})?
```
 no pude funcionar nunca de forma aislada, ya que se basa en criterios muy amplios y laxos como el hecho de empezar por ciertos caracteres, tener determinada medida, no contener dígitos, etc. Sin embargo, si sabemos que en cierta posición de un patrón textual aparecerá una cifra escrita en letras, conseguiremos que funcione casi siempre. Por ejemplo, Si sabemos que en la frase "Además, [CANTIDAD] buques de la costa ..." el concepto CANTIDAD  se expresa con letras, una composición como 
```regex
^Adem.s[,.;] ({##acr_alfa_number##}) buques de la costa (.*)$
```
funcionaría perfectamente. En cambio, esta otra no sería capaz de detectar el valor esperado. 
```regex
^(.*)({##acr_alfa_number##})(.*)$
```
No hace falta usar muletas excesivamente fuertes como las usadas en la primera expresión. Por ensayo y error podemos flexibilizarlas, hasta encontrar el grado de definición que maximice las coincidencias.

A continuación mostraremos las principales expresiones regulares genéricas para ser usadas como componentes de otras más específicas. 

1. Generales
	 - **idem**:  busca equivalencias de la palabra *"idem"*: (id., id, Id., idem, ...)
	 - **ocr_alfa_number**:  Busca números escritos en letra como "Uno", "treinta y tres", "dieciocho", etc. con un criterio muy amplio. Necesita "muletas" a ambos lados para asegurar que en la posición debe haber una cifra escrita con letras.
	 - **ocr_digit_little**: Versión corta del concepto dígito. Esta expresión amplia el concepto añadiendo ciertos caracteres parecidos, visualmente, a dígitos. La cantidad de caracteres añadidos no es muy grande, lo que evita confusiones. Es especialmente útil cuando el OCR tiene cierta calidad y cuando se detectan problemas con algunas otras versiones del mismo concepto, más extensas.
	 - **ocr_digit_no_blanc**: Esta es una versión extensa del concepto dígito. Se aconseja usar de entrada y cambiar a la anterior, en caso de detectar problemas. 
	 - **ocr_digit_plus_blanc**: En algunos OCR de muy mala calidad, algunas cifras pueden aparecer con algún dígito eliminado quedando un espacio en blanco entre dos dígitos, de manera que solo se detecta una parte de la cifra. Esta expresión añade un espacio en blanco y por tanto, es capaz de capturar toda la cifra entera. Debe usarse con cautela porque podría llevar a error. Es importante que se use con muletas que ayuden a detectar la posición de la búsqueda dentro del patrón y sobre todo, evitar aquellos casos donde pudieran existir dos cifras juntas. 
	 - **ocr_capital_letter**: Esta expresión detecta letras mayúsculas con alguna ampliación como los caracteres *7*, *5*, *6* o */* . 
	 - **personal_name**: detecta un nombre completo de persona (nombre y uno o dos apellidos). Admite nombres como: Juan Hernández de Arias, Ramón  Sánchez-Colomer de la Vega, Roberto di Sardo, etc.
	 - **hyphen_proper_noun**:  Detecta un nombre propia. Se basa en detectar que la primera letra comienza por mayúscula, pero además admite dentro el nombre caracteres como el guion que aparece en algunos apellidos como "Sánchez-Colomer".
2. Específicas de barcos
	- **boat_fact_boat_type**: Pensada para detectar tipos de barcos de forma muy genérica. Necesita muletas. 
	- **boat_fact_harbor**: Detecta nombres de puertos simples o compuestos junto con el listado de escalas si se describen (Cádiz, Cartagena y Valencia) o con expresiones propias de puertos como "Cadiz y su carrera".
	- **boat_fact_in_addition**: Detecta varias formas de la palabra "*Además*" cuando se encuentra al inicio de un párrafo y, por tanto, comienza por mayúscula. Puede usarse como muleta de otras expresiones.
	- **boat_fact_of_the_coast**: Detecta expresiones como "buques de la costa" con múltiples variantes. Se usa como muleta de otras expresiones. Aunque es específica del Diario de Barcelona, se ha dejado como expresión de barcos por si en algún otro periódico se repite la frase. En caso de que no se repita se pasará a la carpeta del Diario de Barcelona
	- **boat_fact_vessel**: Busca el concepto barco/embarcación/buque/...
	- **contains_anteayer**, **contains_ayer**, **contains_hoy**: Permite descubrir, dentro de una frase, la cual deba contener un espacio de tiempo o momento relativo, si e tiempo se refiere a hoy, ayer o anteayer.
	- **embarcaciones**: Expresión muy flexible, pero fuerte para detectar la palabra embarcaciones. Puede usarse como muleta de otras expresiones.
	- **is_page_number**: Detecta si un texto puede ser considerado como el número de página de una publicación. Básicamente, se usa para conseguir unir varias páginas sin ruido generado por la numeración de la página al inicio de final de la misma.
	- **llegadas**: detecta la palabra llegadas de un modo muy flexible, pero suficientemente fuerte como para poderla usar como muleta de otras.
	- **mercantes**: Detecta la palabra mercantes. Por su flexibilidad y fortaleza puede usarse como muleta.
	- **ocr_digit**: Alias de ocr_digit_no_blanc.
	- **puerto**: Muleta que detecta la palabra puerto.
	- **start_with_idem**: Expresión específica para detectar el concepto idem de forma amplia, pero forzando que sea inicio de frase para poder usarse como muleta y detector de dato, a la vez.


### Ejemplo
