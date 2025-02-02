'''
Sistema de clasificacion de las enfermedades de la piel 
por medio de imagenes

Autor: Jesser Lemus
'''
# Importamos los modulos y librerias necesarias
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from time import sleep
import re

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

class clasificacion_enfermedades():

    def inicialize_images(self, path):
        
        # Definimos un valor de cuenta, para que se incremente cuando encuentre un directorio o una imagen
        # Definimos un prev_root, como metodo de control al pasar de direccion de directorio
        # dirs_name es un arreglo que guarda los nombres de los directorios
        # dir_count es un arreglo que guarda la cuenta de las imagenes encontradas en un directorio
        count = 0
        prev_root = ''
        dirs_name = []
        dir_count = []

        # Para recorrer el directorio usamos la funcion os.walk en un for
        # Donde root representa la direccion raiz donde se encuentra actualemente
        # dirs es el nombre de los directorios recorridos
        # files al archivo que apunta en ese momento se a donde esta apunto 
        print("LEYENDO IMAGENES....")
        for root, dirs, files in os.walk(path):
            for filename in files:
                # La funcion re.search busca si hay algun archivo de tipo jpg|png o jpeg, de ser el caso
                # Se aumenta el valor de la variable count
                if re.search("\.(jpg|png|jpeg)$", filename):
                    count += 1

                    # Prev_root sirve como un metodo de control para cuando la direccion del directorio 
                    # Haya cambiado, esto significa que debemos volver a realizar la cuenta para la siguiente direccion
                    if prev_root != root:
                        prev_root = root
                        dir_count.append(count)
                        count = 0
            # En la siguiente loop se guardan los nombres de los directorios a un nuevo arreglo
            for name_dirs in dirs:
                dirs_name.append(name_dirs)
            
        # Al ejecutar el for que recorre todos los directorios en busca de imaganes, 
        dir_count.append(count)
        dir_count = dir_count[1:]
        dir_count[0] = dir_count[0] + 1

        return dirs_name, dir_count


    def imprimir_imagenes(self, count, name):
        
        # Formato para imprimir la informacion 
        # Aqui estamos usando el arreglo de nombres y el arregle con el numero de imagenes por categoria
        print("CATAGORIAS ENCONTRADOS", len(name))
        print("=========================================================================================")
        print('{:<70}{}'.format("NOMBRE DEL CATEGORIAS","NUMERO DE IMAGENES"))
        print("=========================================================================================")
        for i in range(len(name)):
            print('{:<70}{}'.format(name[i], count[i]), sep='. ')

        print("=========================================================================================")
        print('{:<70}{}'.format("TOTAL DE IMAGENES ENCONTRADAS", sum(count)))

    def modelo_clasificacion(self, path):

        # Cargar imagenes
        imagenes_train = tf.keras.preprocessing.image_dataset_from_directory(
            path,
            validation_split = 0.2,
            seed=123,
            subset="training",
            image_size=(256, 256))

        imagenes_val = tf.keras.preprocessing.image_dataset_from_directory(
            path,
            validation_split = 0.2,
            seed=123,
            subset="validation",
            image_size=(256, 256))

        # Sistema de control de la existencia de un modelo entrenado
        print("=========================================================================================")
        print("BUSCANDO MODELO...")
        print("=========================================================================================")
        sleep(1)

        if not os.path.exists('Modelo/skin_diseases.h5'):
            
            print("Modelo no encontrado, ajustando parametros de entrenamiento")
            sleep(1)
            # Cache las imagenes en memoria
            AUTOTUNE = tf.data.AUTOTUNE

            imagenes_train = imagenes_train.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
            imagenes_val = imagenes_val.cache().prefetch(buffer_size=AUTOTUNE)

            num_class = 15

            # Definimos el modelo CNN de tres capas con una activacion relu
            model = Sequential([
                    layers.experimental.preprocessing.Rescaling(1./255),
                    layers.Conv2D(32, 3, padding='same', activation='relu'),
                    layers.MaxPooling2D(),
                    layers.Conv2D(32, 3, padding='same', activation='relu'),
                    layers.MaxPooling2D(),
                    layers.Conv2D(32, 3, padding='same', activation='relu'),
                    layers.MaxPooling2D(),
                    layers.Dropout(0.2),
                    layers.Flatten(),
                    layers.Dense(128, activation='relu'),
                    layers.Dense(num_class)])

            #Compilamos el modelo
            model.compile(optimizer='adam', 
                        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), 
                        metrics=['accuracy'])

            model.fit(
                imagenes_train,
                validation_data=imagenes_val,
                epochs = 10
                )

            os.mkdir('Modelo')
            model.save('Modelo/skin_diseases.h5')
            print("Evaluando el modelo...")
            perdida, precision = model.evaluate(imagenes_train, verbose=2)
            print("La precision del modelo es: {:5.2f}%".format(100 * precision))

        else:

            print("¡Modelo encontrado!")
            op = input("¿Desea imprimir la precision del modelo entrenado? [s/N]: ")

            if op == 's' or op == 'S':
                skin_model = tf.keras.models.load_model('Modelo/skin_diseases.h5')
                print("Evaluando el modelo...")
                perdida, precision = skin_model.evaluate(imagenes_train, verbose=2)
                print("La precision del modelo es: {:5.2f}".format(100 * precision))

    def precision(self, class_name):

        print("CLASIFICACION DE IMAGEN")
        # Cargamos el modelo
        skin_model_p = tf.keras.models.load_model('Modelo/skin_diseases.h5')
        
        # Ahora con el modelo entrenado se puede predecir imagenes que no esten en el dataset original
        # Cargamos la una nueva imagen
        img_pruebas_path = os.path.join(os.getcwd(), 'Prueba_img/vascular_test.jpg')
        img_prueba = keras.preprocessing.image.load_img(img_pruebas_path, target_size=(256, 256))

        # 
        img_prueba_array = keras.preprocessing.image.img_to_array(img_prueba)
        img_prueba_array = tf.expand_dims(img_prueba_array, 0)

        # Realizamos la prediccion con la imagen
        prediccion = skin_model_p.predict(img_prueba_array)
        score = tf.nn.softmax(prediccion[0])

        # Realizamos la impresion de los resultados que predijo el modelo y su precision
        print("Se ha detectado la enfermedad {} con una confiabilidad del {:.2f}%"
            .format(class_name[np.argmax(score)], 100 * np.max(score)))
            
if __name__ == '__main__':
    
    carga = clasificacion_enfermedades()
    # Determinamos la direccion de las imagenes para brindar informacion de las categorias
    # os.getcwd obtiene la direccion actual del directorio actual
    path_skindeseases = os.path.join(os.getcwd(),'Dataset/skin_diseases/')
    dirs_nombre, dirs_cuenta = carga.inicialize_images(path_skindeseases)
    print("=========================================================================================")
    # Imprimir la informacion
    option = input("¿Desea imprimir la informacion detallada de las imagenes? [s/N]: ")
    if option == 'S' or option == 's':
        carga.imprimir_imagenes(dirs_cuenta, dirs_nombre)
    print("=========================================================================================")
    # Entrena modelo si no se ha hecho antes
    carga.modelo_clasificacion(path_skindeseases)
    print("=========================================================================================")
    # Imprime la prediccion de una imagen externa al dataset original
    carga.precision(dirs_nombre)
    print("=========================================================================================")
